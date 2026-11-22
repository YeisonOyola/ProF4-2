
"""Software FJ Hotel
Sistema académico de gestión hotelera desarrollado con Python y Tkinter.

Alcance: clientes, habitaciones, salas, alquiler de equipos, asesorías,
reservas, disponibilidad, excepciones personalizadas, registro de eventos
(logs) y pruebas automáticas de demostración. No utiliza bases de datos.
"""

import logging
import re
import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path


# ============================================================================
# 1. CONFIGURACIÓN GENERAL Y REGISTRO DE EVENTOS
# ============================================================================

NOMBRE_SISTEMA = "Software FJ Hotel"
ARCHIVO_LOG = Path(__file__).with_name("software_fj.log")

logging.basicConfig(
    filename=str(ARCHIVO_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("SoftwareFJHotel")


# ============================================================================
# 2. EXCEPCIONES PERSONALIZADAS
# ============================================================================

class SoftwareFJError(Exception):
    """Excepción base para los errores controlados de la aplicación."""


class DatosIncompletosError(SoftwareFJError):
    """Se produce cuando falta un dato obligatorio."""


class ClienteInvalidoError(SoftwareFJError):
    """Se produce cuando los datos de un cliente no son válidos."""


class ClienteDuplicadoError(SoftwareFJError):
    """Se produce cuando ya existe un cliente con esa identificación."""


class ServicioNoDisponibleError(SoftwareFJError):
    """Se produce cuando un servicio o recurso no está disponible."""


class ReservaInvalidaError(SoftwareFJError):
    """Se produce cuando los datos o el estado de una reserva son inválidos."""


class OperacionNoPermitidaError(SoftwareFJError):
    """Se produce cuando una operación no está permitida por las reglas."""


# ============================================================================
# 3. FUNCIONES AUXILIARES DE VALIDACIÓN Y FORMATO
# ============================================================================

def convertir_fecha(valor):
    """Convierte una fecha YYYY-MM-DD en date y encadena errores de formato."""
    try:
        return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError) as error:
        raise ReservaInvalidaError(
            "La fecha debe tener el formato AAAA-MM-DD (por ejemplo, 2026-12-20)."
        ) from error


def convertir_hora(valor):
    """Valida una hora en formato de 24 horas HH:MM."""
    try:
        return datetime.strptime(str(valor).strip(), "%H:%M").time()
    except (TypeError, ValueError) as error:
        raise ReservaInvalidaError("La hora debe tener el formato HH:MM.") from error


def formato_dinero(valor):
    """Presenta un valor numérico como pesos colombianos."""
    return "$" + f"{int(round(valor)):,}".replace(",", ".") + " COP"


def validar_texto_obligatorio(valor, nombre_campo):
    """Comprueba que un texto obligatorio no esté vacío."""
    if valor is None or not str(valor).strip():
        raise DatosIncompletosError(f"El campo {nombre_campo} es obligatorio.")
    return str(valor).strip()


# ============================================================================
# 4. ABSTRACCIÓN: ENTIDAD Y CLIENTE
# ============================================================================

class Entidad(ABC):
    """Clase abstracta con los datos comunes de las personas del sistema."""

    def __init__(self, identificacion, nombre, correo, telefono):
        self.__identificacion = str(identificacion).strip()
        self.__nombre = str(nombre).strip()
        self.__correo = str(correo).strip().lower()
        self.__telefono = str(telefono).strip()

    def obtener_identificacion(self):
        """Devuelve la identificación sin exponer directamente el atributo."""
        return self.__identificacion

    def obtener_nombre(self):
        """Devuelve el nombre de la entidad."""
        return self.__nombre

    def obtener_correo(self):
        """Devuelve el correo electrónico."""
        return self.__correo

    def obtener_telefono(self):
        """Devuelve el teléfono de contacto."""
        return self.__telefono

    @abstractmethod
    def mostrar_informacion(self):
        """Cada clase concreta debe definir cómo presenta su información."""
        raise NotImplementedError


class Cliente(Entidad):
    """Representa a un huésped o cliente externo del hotel."""

    def __init__(self, identificacion, nombre, correo, telefono):
        self.validar_datos(identificacion, nombre, correo, telefono)
        super().__init__(identificacion, nombre, correo, telefono)
        self.__fecha_registro = datetime.now()
        logger.info("Se creó el cliente %s", identificacion)

    @staticmethod
    def validar_datos(identificacion, nombre, correo, telefono):
        """Valida identificación, nombre, correo y teléfono."""
        if not all([identificacion, nombre, correo, telefono]):
            raise DatosIncompletosError("Todos los datos del cliente son obligatorios.")
        if not str(identificacion).strip().isdigit():
            raise ClienteInvalidoError("La identificación debe contener solo números.")
        if len(str(nombre).strip()) < 2:
            raise ClienteInvalidoError("El nombre debe tener al menos dos caracteres.")
        patron_correo = r"^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$"
        if not re.match(patron_correo, str(correo).strip()):
            raise ClienteInvalidoError("El correo electrónico no tiene un formato válido.")
        telefono_limpio = re.sub(r"[\s+()-]", "", str(telefono))
        if not telefono_limpio.isdigit() or not 7 <= len(telefono_limpio) <= 15:
            raise ClienteInvalidoError("El teléfono debe contener entre 7 y 15 dígitos.")

    def obtener_fecha_registro(self):
        """Devuelve la fecha y hora de registro."""
        return self.__fecha_registro

    def mostrar_informacion(self):
        """Implementa el método abstracto de Entidad."""
        return (
            f"{self.obtener_nombre()} | CC: {self.obtener_identificacion()} | "
            f"{self.obtener_correo()} | Tel: {self.obtener_telefono()}"
        )


# ============================================================================
# 5. SERVICIOS ABSTRACTOS Y SUS ESPECIALIZACIONES
# ============================================================================

class Servicio(ABC):
    """Clase abstracta para los servicios que ofrece Software FJ Hotel."""

    def __init__(self, codigo, nombre, tarifa, descripcion=""):
        self.codigo = validar_texto_obligatorio(codigo, "código")
        self.nombre = validar_texto_obligatorio(nombre, "nombre del servicio")
        self.tarifa = float(tarifa)
        self.descripcion = str(descripcion)
        if self.tarifa < 0:
            raise ServicioNoDisponibleError("La tarifa no puede ser negativa.")

    @abstractmethod
    def calcular_costo(self, cantidad=1, descuento=0):
        """Calcula el costo según la modalidad concreta del servicio."""
        raise NotImplementedError

    @abstractmethod
    def obtener_tipo(self):
        """Devuelve el tipo de servicio."""
        raise NotImplementedError


class ReservaHabitacion(Servicio):
    """Servicio de alojamiento en habitación individual o doble."""

    def __init__(self, codigo, nombre, tipo, capacidad, tarifa_noche):
        super().__init__(codigo, nombre, tarifa_noche, "Alojamiento turístico")
        self.tipo = tipo
        self.capacidad = int(capacidad)
        if self.tipo not in ("Individual", "Doble"):
            raise ServicioNoDisponibleError("El tipo debe ser Individual o Doble.")
        if self.capacidad not in (1, 2):
            raise ServicioNoDisponibleError("La capacidad debe ser de una o dos personas.")

    def calcular_costo(self, cantidad=1, descuento=0):
        """Calcula noches por tarifa; descuento es un porcentaje entre 0 y 100."""
        noches = int(cantidad)
        if noches <= 0 or not 0 <= float(descuento) <= 100:
            raise ReservaInvalidaError("Noches o descuento fuera del rango permitido.")
        return noches * self.tarifa * (1 - float(descuento) / 100)

    def obtener_tipo(self):
        return "Habitación"


class ReservaSala(Servicio):
    """Servicio de alquiler de salas para reuniones y eventos."""

    def __init__(self, codigo, nombre, capacidad, tarifa_hora):
        super().__init__(codigo, nombre, tarifa_hora, "Sala para reuniones o eventos")
        self.capacidad = int(capacidad)

    def calcular_costo(self, cantidad=1, descuento=0):
        """Calcula horas de alquiler con descuento porcentual opcional."""
        horas = float(cantidad)
        if horas <= 0 or not 0 <= float(descuento) <= 100:
            raise ReservaInvalidaError("Horas o descuento fuera del rango permitido.")
        return horas * self.tarifa * (1 - float(descuento) / 100)

    def obtener_tipo(self):
        return "Sala"


class AlquilerEquipos(Servicio):
    """Servicio de alquiler de equipos por día y con inventario limitado."""

    def __init__(self, codigo, nombre, unidades, tarifa_dia):
        super().__init__(codigo, nombre, tarifa_dia, "Alquiler de equipos")
        self.unidades = int(unidades)
        if self.unidades < 1:
            raise ServicioNoDisponibleError("Debe existir al menos una unidad disponible.")

    def calcular_costo(self, cantidad=1, descuento=0, unidades=1):
        """Permite calcular días y unidades; simula sobrecarga con parámetros opcionales."""
        dias = int(cantidad)
        numero_unidades = int(unidades)
        if dias <= 0 or numero_unidades <= 0 or not 0 <= float(descuento) <= 100:
            raise ReservaInvalidaError("Días, unidades o descuento fuera del rango permitido.")
        return dias * numero_unidades * self.tarifa * (1 - float(descuento) / 100)

    def obtener_tipo(self):
        return "Equipo"


class AsesoriaEspecializada(Servicio):
    """Servicio de asesorías por hora."""

    def __init__(self, codigo, nombre, tarifa_hora):
        super().__init__(codigo, nombre, tarifa_hora, "Asesoría especializada")

    def calcular_costo(self, cantidad=1, descuento=0):
        """Calcula horas de asesoría con descuento porcentual opcional."""
        horas = float(cantidad)
        if horas <= 0 or not 0 <= float(descuento) <= 100:
            raise ReservaInvalidaError("Horas o descuento fuera del rango permitido.")
        return horas * self.tarifa * (1 - float(descuento) / 100)

    def obtener_tipo(self):
        return "Asesoría"


# ============================================================================
# 6. RESERVA: ESTADOS Y REGLAS DE NEGOCIO
# ============================================================================

class Reserva:
    """Representa una reserva de un servicio para un cliente."""

    ESTADOS = ("Pendiente", "Confirmada", "Cancelada", "Finalizada")

    def __init__(self, codigo, cliente, servicio, fecha_inicio, fecha_fin,
                 cantidad=1, personas=1, hora_inicio="09:00", hora_fin="10:00",
                 descuento=0, unidades=1):
        self.codigo = str(codigo)
        self.cliente = cliente
        self.servicio = servicio
        self.fecha_inicio = convertir_fecha(fecha_inicio)
        self.fecha_fin = convertir_fecha(fecha_fin)
        self.cantidad = float(cantidad)
        self.personas = int(personas)
        self.hora_inicio = convertir_hora(hora_inicio)
        self.hora_fin = convertir_hora(hora_fin)
        self.descuento = float(descuento)
        self.unidades = int(unidades)
        self.estado = "Pendiente"
        self.fecha_creacion = datetime.now()
        self.validar_datos()
        self.costo = self.calcular_total()

    def validar_datos(self):
        """Valida fechas, capacidad, cantidades y parámetros de la reserva."""
        if not isinstance(self.cliente, Cliente):
            raise ReservaInvalidaError("Debe seleccionar un cliente registrado.")
        if not isinstance(self.servicio, Servicio):
            raise ReservaInvalidaError("Debe seleccionar un servicio válido.")
        if self.fecha_inicio < date.today():
            raise ReservaInvalidaError("La fecha de inicio no puede estar en el pasado.")
        if self.fecha_fin <= self.fecha_inicio:
            raise ReservaInvalidaError("La fecha final debe ser posterior a la inicial.")
        if self.personas < 1:
            raise ReservaInvalidaError("El número de personas debe ser al menos uno.")
        if not 0 <= self.descuento <= 100:
            raise ReservaInvalidaError("El descuento debe estar entre 0 y 100.")
        if isinstance(self.servicio, ReservaHabitacion) and self.personas > self.servicio.capacidad:
            raise ReservaInvalidaError("La cantidad de huéspedes supera la capacidad de la habitación.")
        if isinstance(self.servicio, ReservaSala) and self.personas > self.servicio.capacidad:
            raise ReservaInvalidaError("La cantidad de asistentes supera la capacidad de la sala.")
        if isinstance(self.servicio, AlquilerEquipos):
            if self.unidades < 1 or self.unidades > self.servicio.unidades:
                raise ReservaInvalidaError("La cantidad de equipos solicitada no es válida.")
        if isinstance(self.servicio, (ReservaSala, AsesoriaEspecializada)):
            if self.hora_fin <= self.hora_inicio:
                raise ReservaInvalidaError("La hora final debe ser posterior a la hora inicial.")

    def calcular_total(self):
        """Calcula el precio mediante polimorfismo según el tipo de servicio."""
        if isinstance(self.servicio, ReservaHabitacion):
            noches = (self.fecha_fin - self.fecha_inicio).days
            return self.servicio.calcular_costo(noches, self.descuento)
        if isinstance(self.servicio, AlquilerEquipos):
            dias = (self.fecha_fin - self.fecha_inicio).days
            return self.servicio.calcular_costo(dias, self.descuento, self.unidades)
        if isinstance(self.servicio, (ReservaSala, AsesoriaEspecializada)):
            duracion = (datetime.combine(self.fecha_inicio, self.hora_fin)
                        - datetime.combine(self.fecha_inicio, self.hora_inicio)).seconds / 3600
            return self.servicio.calcular_costo(duracion, self.descuento)
        raise ServicioNoDisponibleError("No se reconoce el tipo de servicio.")

    def confirmar(self):
        """Confirma una reserva que se encuentre pendiente."""
        if self.estado != "Pendiente":
            raise OperacionNoPermitidaError("Solo se pueden confirmar reservas pendientes.")
        self.estado = "Confirmada"
        logger.info("Reserva %s confirmada", self.codigo)

    def cancelar(self):
        """Cancela una reserva pendiente o confirmada."""
        if self.estado not in ("Pendiente", "Confirmada"):
            raise OperacionNoPermitidaError("Esta reserva no se puede cancelar.")
        self.estado = "Cancelada"
        logger.info("Reserva %s cancelada", self.codigo)

    def finalizar(self):
        """Finaliza una reserva confirmada cuando termina su periodo."""
        if self.estado != "Confirmada":
            raise OperacionNoPermitidaError("Solo se pueden finalizar reservas confirmadas.")
        if date.today() < self.fecha_fin:
            raise OperacionNoPermitidaError("La fecha de salida o finalización aún no ha llegado.")
        self.estado = "Finalizada"
        logger.info("Reserva %s finalizada", self.codigo)

    def mostrar_informacion(self):
        """Devuelve un resumen de la reserva."""
        return (f"{self.codigo} | {self.cliente.obtener_nombre()} | "
                f"{self.servicio.obtener_tipo()}: {self.servicio.nombre} | "
                f"{self.fecha_inicio} a {self.fecha_fin} | {self.estado} | "
                f"{formato_dinero(self.costo)}")


# ============================================================================
# 7. SISTEMA HOTEL: LISTAS INTERNAS, INVENTARIO Y DISPONIBILIDAD
# ============================================================================

class SistemaHotel:
    """Coordina clientes, catálogo de servicios, reservas e inventarios."""

    def __init__(self):
        self.__clientes = []
        self.__servicios = []
        self.__reservas = []
        self.__contador_reservas = 1
        self.cargar_inventario_inicial()

    def cargar_inventario_inicial(self):
        """Crea el inventario demostrativo con tarifas fijas de referencia."""
        for numero in range(101, 106):
            self.__servicios.append(ReservaHabitacion(
                f"H{numero}", f"Habitación {numero}", "Individual", 1, 100000))
        for numero in range(201, 206):
            self.__servicios.append(ReservaHabitacion(
                f"H{numero}", f"Habitación {numero}", "Doble", 2, 160000))
        self.__servicios.extend([
            ReservaSala("S01", "Sala Guatavita", 20, 60000),
            ReservaSala("S02", "Sala Siecha", 40, 90000),
            AlquilerEquipos("E01", "Portátil", 5, 35000),
            AlquilerEquipos("E02", "Proyector", 3, 25000),
            AlquilerEquipos("E03", "Equipo audiovisual", 2, 45000),
            AsesoriaEspecializada("A01", "Asesoría turística", 50000),
            AsesoriaEspecializada("A02", "Asesoría tecnológica", 80000),
            AsesoriaEspecializada("A03", "Asesoría administrativa", 70000),
        ])
        logger.info("Inventario inicial cargado")

    def registrar_cliente(self, identificacion, nombre=None, correo=None, telefono=None):
        """Registra un cliente; acepta un objeto Cliente o sus cuatro datos.

        La firma con argumentos opcionales permite dos formas de invocación,
        simulando sobrecarga de métodos en Python.
        """
        if isinstance(identificacion, Cliente) and nombre is None:
            cliente = identificacion
        else:
            cliente = Cliente(identificacion, nombre, correo, telefono)
        if self.buscar_cliente(cliente.obtener_identificacion()):
            logger.warning("Identificación duplicada: %s", cliente.obtener_identificacion())
            raise ClienteDuplicadoError("Ya existe un cliente con esa identificación.")
        self.__clientes.append(cliente)
        logger.info("Cliente agregado al sistema: %s", cliente.obtener_identificacion())
        return cliente

    def buscar_cliente(self, identificacion):
        """Busca y devuelve un cliente; devuelve None si no existe."""
        for cliente in self.__clientes:
            if cliente.obtener_identificacion() == str(identificacion).strip():
                return cliente
        return None

    def eliminar_cliente(self, identificacion):
        """Elimina un cliente que no tenga reservas pendientes o confirmadas."""
        cliente = self.buscar_cliente(identificacion)
        if cliente is None:
            raise ClienteInvalidoError("No se encontró el cliente solicitado.")
        if any(r.cliente is cliente and r.estado in ("Pendiente", "Confirmada")
               for r in self.__reservas):
            raise OperacionNoPermitidaError(
                "No se puede eliminar un cliente con reservas activas.")
        self.__clientes.remove(cliente)
        logger.info("Cliente eliminado: %s", identificacion)

    def listar_clientes(self):
        return list(self.__clientes)

    def listar_servicios(self, tipo=None):
        """Lista servicios; el parámetro opcional permite filtrar por tipo."""
        if tipo is None or tipo == "Todos":
            return list(self.__servicios)
        return [s for s in self.__servicios if s.obtener_tipo() == tipo]

    def buscar_servicio(self, codigo):
        for servicio in self.__servicios:
            if servicio.codigo == str(codigo).strip():
                return servicio
        return None

    @staticmethod
    def se_superponen(inicio_a, fin_a, inicio_b, fin_b):
        """Devuelve True si dos intervalos de fechas se cruzan."""
        return inicio_a < fin_b and inicio_b < fin_a

    def comprobar_disponibilidad(self, servicio, inicio, fin, hora_inicio,
                                 hora_fin, unidades=1, ignorar_reserva=None):
        """Comprueba solapamientos de habitaciones, salas, asesorías y equipos."""
        activas = [r for r in self.__reservas
                   if r.estado in ("Pendiente", "Confirmada")
                   and r.servicio.codigo == servicio.codigo
                   and r is not ignorar_reserva]
        for reserva in activas:
            cruza_fechas = self.se_superponen(inicio, fin,
                                               reserva.fecha_inicio, reserva.fecha_fin)
            if not cruza_fechas:
                continue
            if isinstance(servicio, AlquilerEquipos):
                unidades_usadas = sum(
                    r.unidades for r in activas
                    if self.se_superponen(inicio, fin, r.fecha_inicio, r.fecha_fin)
                )
                if unidades_usadas + unidades > servicio.unidades:
                    raise ServicioNoDisponibleError(
                        f"No hay suficientes unidades de {servicio.nombre} para esas fechas.")
            elif isinstance(servicio, (ReservaSala, AsesoriaEspecializada)):
                misma_fecha = inicio == reserva.fecha_inicio
                cruza_horas = hora_inicio < reserva.hora_fin and reserva.hora_inicio < hora_fin
                if misma_fecha and cruza_horas:
                    raise ServicioNoDisponibleError(
                        f"{servicio.nombre} ya está reservado en ese horario.")
            else:
                raise ServicioNoDisponibleError(
                    f"{servicio.nombre} no está disponible en esas fechas.")

    def crear_reserva(self, identificacion_cliente, codigo_servicio,
                      fecha_inicio, fecha_fin, cantidad=1, personas=1,
                      hora_inicio="09:00", hora_fin="10:00", descuento=0,
                      unidades=1):
        """Valida disponibilidad y crea una reserva en estado Pendiente."""
        cliente = self.buscar_cliente(identificacion_cliente)
        servicio = self.buscar_servicio(codigo_servicio)
        if cliente is None:
            raise ClienteInvalidoError("El cliente no está registrado.")
        if servicio is None:
            raise ServicioNoDisponibleError("El servicio seleccionado no existe.")
        reserva = Reserva(
            f"R{self.__contador_reservas:04d}", cliente, servicio,
            fecha_inicio, fecha_fin, cantidad, personas, hora_inicio,
            hora_fin, descuento, unidades)
        self.comprobar_disponibilidad(
            servicio, reserva.fecha_inicio, reserva.fecha_fin,
            reserva.hora_inicio, reserva.hora_fin, reserva.unidades)
        self.__reservas.append(reserva)
        self.__contador_reservas += 1
        logger.info("Reserva %s creada en estado Pendiente", reserva.codigo)
        return reserva

    def obtener_reserva(self, codigo):
        for reserva in self.__reservas:
            if reserva.codigo == str(codigo).strip():
                return reserva
        return None

    def confirmar_reserva(self, codigo):
        reserva = self.obtener_reserva(codigo)
        if reserva is None:
            raise ReservaInvalidaError("No se encontró la reserva.")
        reserva.confirmar()
        return reserva

    def cancelar_reserva(self, codigo):
        reserva = self.obtener_reserva(codigo)
        if reserva is None:
            raise ReservaInvalidaError("No se encontró la reserva.")
        reserva.cancelar()
        return reserva

    def finalizar_reserva(self, codigo):
        reserva = self.obtener_reserva(codigo)
        if reserva is None:
            raise ReservaInvalidaError("No se encontró la reserva.")
        reserva.finalizar()
        return reserva

    def listar_reservas(self, estado=None):
        if estado is None or estado == "Todos":
            return list(self.__reservas)
        return [r for r in self.__reservas if r.estado == estado]


# ============================================================================
# 8. PRUEBAS AUTOMÁTICAS: MÁS DE DIEZ OPERACIONES
# ============================================================================

def ejecutar_pruebas():
    """Ejecuta pruebas independientes con datos temporales en memoria."""
    sistema = SistemaHotel()
    resultados = []

    def prueba(nombre, accion, debe_fallar=False):
        try:
            accion()
            if debe_fallar:
                resultados.append((nombre, False, "Se esperaba un error y no ocurrió."))
            else:
                resultados.append((nombre, True, "Correcto"))
        except Exception as error:
            if debe_fallar:
                resultados.append((nombre, True, f"Error controlado: {error}"))
            else:
                resultados.append((nombre, False, str(error)))

    prueba("1. Registro de cliente válido", lambda: sistema.registrar_cliente(
        "900000001", "Cliente Prueba Uno", "uno@correo.com", "3001112233"))
    prueba("2. Registro de identificación duplicada", lambda: sistema.registrar_cliente(
        "900000001", "Cliente Repetido", "repetido@correo.com", "3001112234"), True)
    prueba("3. Validación de correo inválido", lambda: sistema.registrar_cliente(
        "900000002", "Cliente Dos", "correo-invalido", "3001112235"), True)
    prueba("4. Consulta del inventario", lambda: sistema.listar_servicios())
    prueba("5. Búsqueda de cliente existente", lambda: sistema.buscar_cliente("900000001"))
    prueba("6. Búsqueda de cliente inexistente", lambda: (
        sistema.buscar_cliente("999999999") is None))
    prueba("7. Reserva de habitación disponible", lambda: sistema.crear_reserva(
        "900000001", "H101", "2099-05-10", "2099-05-12", personas=1))
    prueba("8. Rechazo de habitación ocupada", lambda: sistema.crear_reserva(
        "900000001", "H101", "2099-05-11", "2099-05-13", personas=1), True)
    prueba("9. Confirmación de reserva", lambda: sistema.confirmar_reserva("R0001"))
    prueba("10. Cancelación de reserva", lambda: sistema.cancelar_reserva("R0001"))
    prueba("11. Reserva de sala", lambda: sistema.crear_reserva(
        "900000001", "S01", "2099-06-10", "2099-06-11",
        hora_inicio="09:00", hora_fin="11:00", personas=8))
    prueba("12. Alquiler de equipos", lambda: sistema.crear_reserva(
        "900000001", "E01", "2099-07-10", "2099-07-12", unidades=2))
    prueba("13. Reserva de asesoría", lambda: sistema.crear_reserva(
        "900000001", "A01", "2099-08-10", "2099-08-11",
        hora_inicio="10:00", hora_fin="11:00"))
    prueba("14. Rechazo de fechas invertidas", lambda: sistema.crear_reserva(
        "900000001", "H102", "2099-09-12", "2099-09-10"), True)
    prueba("15. Rechazo de cliente inexistente", lambda: sistema.crear_reserva(
        "999999999", "H103", "2099-10-10", "2099-10-11"), True)

    aprobadas = sum(1 for _, ok, _ in resultados if ok)
    return resultados, aprobadas, len(resultados)


# ============================================================================
# 9. INTERFAZ GRÁFICA CON TKINTER
# ============================================================================

class AplicacionHotel:
    """Interfaz gráfica principal para administrar Software FJ Hotel."""

    def __init__(self, root):
        self.root = root
        self.sistema = SistemaHotel()
        self.root.title(f"{NOMBRE_SISTEMA} | Gestión hotelera")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.root.configure(bg="#f3f5f8")
        self.configurar_estilos()
        self.crear_interfaz()
        self.actualizar_todo()
        logger.info("Interfaz gráfica iniciada")

    def configurar_estilos(self):
        """Define colores y estilos visuales de la aplicación."""
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TFrame", background="#f3f5f8")
        estilo.configure("Card.TFrame", background="#ffffff")
        estilo.configure("TLabel", background="#f3f5f8", foreground="#17243a",
                         font=("Segoe UI", 10))
        estilo.configure("Title.TLabel", font=("Segoe UI", 20, "bold"),
                         foreground="#14243a", background="#f3f5f8")
        estilo.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#65748b")
        estilo.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        estilo.configure("Accent.TButton", font=("Segoe UI", 9, "bold"),
                         padding=7, background="#c69b45", foreground="#ffffff")
        estilo.map("Accent.TButton", background=[("active", "#ae8434")])
        estilo.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 9, "bold"))

    def crear_interfaz(self):
        """Construye encabezado, indicadores y pestañas."""
        encabezado = tk.Frame(self.root, bg="#14243a", height=82)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)
        tk.Label(encabezado, text="SOFTWARE FJ HOTEL", bg="#14243a", fg="white",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=24, pady=(13, 0))
        tk.Label(encabezado, text="Gestión integral de huéspedes, servicios y reservas",
                 bg="#14243a", fg="#d9e0e9", font=("Segoe UI", 9)).pack(anchor="w", padx=26)

        contenido = ttk.Frame(self.root, padding=18)
        contenido.pack(fill="both", expand=True)
        ttk.Label(contenido, text="Panel de administración", style="Title.TLabel").pack(anchor="w")
        ttk.Label(contenido, text="Hotel turístico · Tarifas de referencia en pesos colombianos",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(2, 12))

        self.indicadores = ttk.Frame(contenido)
        self.indicadores.pack(fill="x", pady=(0, 12))
        self.lbl_clientes = self.crear_tarjeta(self.indicadores, "Clientes", "0")
        self.lbl_servicios = self.crear_tarjeta(self.indicadores, "Servicios", "0")
        self.lbl_reservas = self.crear_tarjeta(self.indicadores, "Reservas", "0")
        self.lbl_pendientes = self.crear_tarjeta(self.indicadores, "Pendientes", "0")

        self.notebook = ttk.Notebook(contenido)
        self.notebook.pack(fill="both", expand=True)
        self.tab_inicio = ttk.Frame(self.notebook, padding=14)
        self.tab_clientes = ttk.Frame(self.notebook, padding=14)
        self.tab_servicios = ttk.Frame(self.notebook, padding=14)
        self.tab_reservas = ttk.Frame(self.notebook, padding=14)
        self.tab_pruebas = ttk.Frame(self.notebook, padding=14)
        self.tab_logs = ttk.Frame(self.notebook, padding=14)
        for tab, nombre in [
            (self.tab_inicio, "Inicio"), (self.tab_clientes, "Clientes"),
            (self.tab_servicios, "Servicios"), (self.tab_reservas, "Reservas"),
            (self.tab_pruebas, "Pruebas"), (self.tab_logs, "Logs"),
        ]:
            self.notebook.add(tab, text=nombre)
        self.crear_tab_inicio()
        self.crear_tab_clientes()
        self.crear_tab_servicios()
        self.crear_tab_reservas()
        self.crear_tab_pruebas()
        self.crear_tab_logs()

    def crear_tarjeta(self, contenedor, titulo, valor):
        """Crea una tarjeta pequeña de indicador."""
        tarjeta = tk.Frame(contenedor, bg="white", highlightbackground="#e1e6ed",
                           highlightthickness=1, padx=16, pady=10)
        tarjeta.pack(side="left", fill="x", expand=True, padx=(0, 9))
        tk.Label(tarjeta, text=titulo.upper(), bg="white", fg="#748197",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        etiqueta = tk.Label(tarjeta, text=valor, bg="white", fg="#14243a",
                            font=("Segoe UI", 20, "bold"))
        etiqueta.pack(anchor="w")
        return etiqueta

    def crear_tab_inicio(self):
        ttk.Label(self.tab_inicio, text="Bienvenido a Software FJ Hotel",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(4, 8))
        texto = (
            "Desde este panel puede registrar huéspedes y clientes externos, consultar el "
            "catálogo de servicios y administrar reservas. Las reservas nuevas quedan en "
            "estado Pendiente hasta que un empleado las confirme.\n\n"
            "Servicios incluidos:\n"
            "• Habitaciones individuales y dobles para alojamiento.\n"
            "• Salas para reuniones y eventos.\n"
            "• Alquiler de portátiles, proyectores y equipos audiovisuales.\n"
            "• Asesorías turísticas, tecnológicas y administrativas.\n\n"
            "La información se conserva en memoria mientras la aplicación está abierta. "
            "El archivo software_fj.log registra eventos y errores; no es una base de datos."
        )
        tk.Label(self.tab_inicio, text=texto, justify="left", anchor="nw",
                 bg="white", fg="#34445b", padx=20, pady=20,
                 font=("Segoe UI", 10), wraplength=900).pack(fill="both", expand=True)

    def crear_tab_clientes(self):
        ttk.Label(self.tab_clientes, text="Registro de clientes",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        formulario = ttk.Frame(self.tab_clientes)
        formulario.pack(fill="x", pady=(0, 10))
        self.ent_id = self.agregar_campo(formulario, "Identificación", 0, 0)
        self.ent_nombre = self.agregar_campo(formulario, "Nombre completo", 0, 2)
        self.ent_correo = self.agregar_campo(formulario, "Correo electrónico", 1, 0)
        self.ent_telefono = self.agregar_campo(formulario, "Teléfono", 1, 2)
        ttk.Button(formulario, text="Registrar cliente", style="Accent.TButton",
                   command=self.registrar_cliente_ui).grid(row=2, column=0, padx=5, pady=8, sticky="w")
        ttk.Button(formulario, text="Limpiar", command=self.limpiar_cliente).grid(
            row=2, column=1, padx=5, pady=8, sticky="w")
        columnas = ("identificacion", "nombre", "correo", "telefono")
        self.tabla_clientes = self.crear_tabla(self.tab_clientes, columnas,
            ("Identificación", "Nombre", "Correo", "Teléfono"), (130, 220, 250, 150))
        ttk.Button(self.tab_clientes, text="Eliminar cliente seleccionado",
                   command=self.eliminar_cliente_ui).pack(anchor="e", pady=8)

    def crear_tab_servicios(self):
        ttk.Label(self.tab_servicios, text="Catálogo de servicios e inventario",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        columnas = ("codigo", "tipo", "nombre", "detalle", "tarifa")
        self.tabla_servicios = self.crear_tabla(self.tab_servicios, columnas,
            ("Código", "Tipo", "Servicio", "Capacidad / unidades", "Tarifa base"),
            (90, 120, 230, 170, 160))
        ttk.Label(self.tab_servicios,
                  text="Las tarifas son valores fijos de referencia definidos para este proyecto académico.",
                  style="Subtitle.TLabel").pack(anchor="w", pady=8)

    def crear_tab_reservas(self):
        ttk.Label(self.tab_reservas, text="Crear y administrar reservas",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        formulario = ttk.Frame(self.tab_reservas)
        formulario.pack(fill="x", pady=4)
        self.cmb_cliente = self.agregar_combo(formulario, "Cliente", 0, 0, [])
        self.cmb_servicio = self.agregar_combo(formulario, "Servicio", 0, 2, [])
        self.ent_inicio = self.agregar_campo(formulario, "Fecha inicial (AAAA-MM-DD)", 1, 0)
        self.ent_fin = self.agregar_campo(formulario, "Fecha final (AAAA-MM-DD)", 1, 2)
        self.ent_personas = self.agregar_campo(formulario, "Personas / asistentes", 2, 0, "1")
        self.ent_hora_inicio = self.agregar_campo(formulario, "Hora inicial (HH:MM)", 2, 2, "09:00")
        self.ent_hora_fin = self.agregar_campo(formulario, "Hora final (HH:MM)", 3, 0, "10:00")
        self.ent_unidades = self.agregar_campo(formulario, "Unidades de equipo", 3, 2, "1")
        ttk.Button(formulario, text="Crear reserva pendiente", style="Accent.TButton",
                   command=self.crear_reserva_ui).grid(row=4, column=0, padx=5, pady=8, sticky="w")
        ttk.Button(formulario, text="Actualizar", command=self.actualizar_todo).grid(
            row=4, column=1, padx=5, pady=8, sticky="w")
        # La barra de acciones se crea ANTES de la tabla para reservarle
        # siempre su espacio. Así los botones no quedan ocultos debajo
        # de la tabla cuando la ventana tiene una altura limitada.
        acciones = ttk.Frame(self.tab_reservas)
        acciones.pack(fill="x", pady=(6, 8))
        ttk.Button(acciones, text="Confirmar", command=self.confirmar_reserva_ui).pack(side="left", padx=3)
        ttk.Button(acciones, text="Cancelar", command=self.cancelar_reserva_ui).pack(side="left", padx=3)
        ttk.Button(acciones, text="Finalizar", command=self.finalizar_reserva_ui).pack(side="left", padx=3)
        ttk.Label(acciones, text="Selecciona una reserva pendiente para administrarla.",
                  style="Subtitle.TLabel").pack(side="right")

        columnas = ("codigo", "cliente", "servicio", "fechas", "estado", "costo")
        self.tabla_reservas = self.crear_tabla(self.tab_reservas, columnas,
            ("Código", "Cliente", "Servicio", "Fechas", "Estado", "Costo"),
            (80, 160, 190, 180, 100, 130))

    def crear_tab_pruebas(self):
        ttk.Label(self.tab_pruebas, text="Validación de requisitos y operaciones",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(self.tab_pruebas,
                  text="Las pruebas usan un sistema temporal separado; no modifican los datos de esta sesión.",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Button(self.tab_pruebas, text="Ejecutar 15 pruebas automáticas",
                   style="Accent.TButton", command=self.ejecutar_pruebas_ui).pack(anchor="w", pady=5)
        self.texto_pruebas = tk.Text(self.tab_pruebas, height=22, wrap="word",
                                     font=("Consolas", 9), bg="white", fg="#26364d")
        self.texto_pruebas.pack(fill="both", expand=True, pady=8)

    def crear_tab_logs(self):
        ttk.Label(self.tab_logs, text="Registro de actividad",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Button(self.tab_logs, text="Actualizar registros", command=self.mostrar_logs_ui).pack(anchor="w")
        self.texto_logs = tk.Text(self.tab_logs, height=24, wrap="word",
                                  font=("Consolas", 9), bg="white", fg="#26364d")
        self.texto_logs.pack(fill="both", expand=True, pady=8)
        self.mostrar_logs_ui()

    def agregar_campo(self, contenedor, etiqueta, fila, columna, valor=""):
        """Crea etiqueta y entrada; devuelve el widget Entry."""
        bloque = ttk.Frame(contenedor)
        bloque.grid(row=fila, column=columna, padx=5, pady=4, sticky="ew")
        ttk.Label(bloque, text=etiqueta).pack(anchor="w")
        entrada = ttk.Entry(bloque, width=31)
        entrada.pack(fill="x", pady=(2, 0))
        if valor:
            entrada.insert(0, valor)
        contenedor.columnconfigure(columna, weight=1)
        return entrada

    def agregar_combo(self, contenedor, etiqueta, fila, columna, valores):
        """Crea un cuadro combinado para seleccionar elementos."""
        bloque = ttk.Frame(contenedor)
        bloque.grid(row=fila, column=columna, padx=5, pady=4, sticky="ew")
        ttk.Label(bloque, text=etiqueta).pack(anchor="w")
        combo = ttk.Combobox(bloque, values=valores, state="readonly", width=29)
        combo.pack(fill="x", pady=(2, 0))
        contenedor.columnconfigure(columna, weight=1)
        return combo

    def crear_tabla(self, contenedor, columnas, encabezados, anchos):
        """Crea una tabla Treeview con barra de desplazamiento vertical."""
        marco = ttk.Frame(contenedor)
        marco.pack(fill="both", expand=True)
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=10)
        for columna, encabezado, ancho in zip(columnas, encabezados, anchos):
            tabla.heading(columna, text=encabezado)
            tabla.column(columna, width=ancho, minwidth=70, anchor="w")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    def limpiar_cliente(self):
        for entrada in (self.ent_id, self.ent_nombre, self.ent_correo, self.ent_telefono):
            entrada.delete(0, "end")

    def registrar_cliente_ui(self):
        try:
            self.sistema.registrar_cliente(
                self.ent_id.get(), self.ent_nombre.get(),
                self.ent_correo.get(), self.ent_telefono.get())
            messagebox.showinfo("Registro exitoso", "El cliente fue registrado correctamente.")
            self.limpiar_cliente()
            self.actualizar_todo()
        except SoftwareFJError as error:
            logger.warning("No se pudo registrar cliente desde la interfaz: %s", error)
            messagebox.showerror("No se pudo registrar", str(error))
        except Exception as error:
            logger.exception("Error inesperado en registro de cliente")
            messagebox.showerror("Error inesperado", str(error))

    def eliminar_cliente_ui(self):
        seleccionado = self.tabla_clientes.selection()
        if not seleccionado:
            messagebox.showwarning("Selección requerida", "Seleccione un cliente de la tabla.")
            return
        identificacion = self.tabla_clientes.item(seleccionado[0], "values")[0]
        if not messagebox.askyesno("Confirmar", f"¿Desea eliminar al cliente {identificacion}?"):
            return
        try:
            self.sistema.eliminar_cliente(identificacion)
            messagebox.showinfo("Operación exitosa", "Cliente eliminado.")
            self.actualizar_todo()
        except SoftwareFJError as error:
            messagebox.showerror("No se pudo eliminar", str(error))

    def crear_reserva_ui(self):
        try:
            cliente_texto = self.cmb_cliente.get()
            servicio_texto = self.cmb_servicio.get()
            if not cliente_texto or not servicio_texto:
                raise DatosIncompletosError("Seleccione un cliente y un servicio.")
            identificacion = cliente_texto.split(" | ")[0]
            codigo = servicio_texto.split(" | ")[0]
            personas = int(self.ent_personas.get() or "1")
            unidades = int(self.ent_unidades.get() or "1")
            reserva = self.sistema.crear_reserva(
                identificacion, codigo, self.ent_inicio.get(), self.ent_fin.get(),
                personas=personas, hora_inicio=self.ent_hora_inicio.get(),
                hora_fin=self.ent_hora_fin.get(), unidades=unidades)
            messagebox.showinfo("Reserva creada",
                f"Reserva {reserva.codigo} creada en estado Pendiente.\n"
                f"Costo estimado: {formato_dinero(reserva.costo)}")
            self.actualizar_todo()
        except (SoftwareFJError, ValueError) as error:
            logger.warning("Error al crear reserva desde interfaz: %s", error)
            messagebox.showerror("No se pudo crear la reserva", str(error))
        except Exception as error:
            logger.exception("Error inesperado al crear reserva")
            messagebox.showerror("Error inesperado", str(error))

    def codigo_reserva_seleccionada(self):
        seleccionado = self.tabla_reservas.selection()
        if not seleccionado:
            raise DatosIncompletosError("Seleccione una reserva de la tabla.")
        return self.tabla_reservas.item(seleccionado[0], "values")[0]

    def confirmar_reserva_ui(self):
        try:
            reserva = self.sistema.confirmar_reserva(self.codigo_reserva_seleccionada())
            messagebox.showinfo("Reserva confirmada", f"La reserva {reserva.codigo} fue confirmada.")
            self.actualizar_todo()
        except SoftwareFJError as error:
            messagebox.showerror("No se pudo confirmar", str(error))

    def cancelar_reserva_ui(self):
        try:
            reserva = self.sistema.cancelar_reserva(self.codigo_reserva_seleccionada())
            messagebox.showinfo("Reserva cancelada", f"La reserva {reserva.codigo} fue cancelada.")
            self.actualizar_todo()
        except SoftwareFJError as error:
            messagebox.showerror("No se pudo cancelar", str(error))

    def finalizar_reserva_ui(self):
        try:
            reserva = self.sistema.finalizar_reserva(self.codigo_reserva_seleccionada())
            messagebox.showinfo("Reserva finalizada", f"La reserva {reserva.codigo} fue finalizada.")
            self.actualizar_todo()
        except SoftwareFJError as error:
            messagebox.showerror("No se pudo finalizar", str(error))

    def actualizar_todo(self):
        """Actualiza indicadores, tablas y listas desplegables."""
        clientes = self.sistema.listar_clientes()
        servicios = self.sistema.listar_servicios()
        reservas = self.sistema.listar_reservas()
        self.lbl_clientes.config(text=str(len(clientes)))
        self.lbl_servicios.config(text=str(len(servicios)))
        self.lbl_reservas.config(text=str(len(reservas)))
        self.lbl_pendientes.config(text=str(sum(r.estado == "Pendiente" for r in reservas)))
        self.vaciar_tabla(self.tabla_clientes)
        for cliente in clientes:
            self.tabla_clientes.insert("", "end", values=(
                cliente.obtener_identificacion(), cliente.obtener_nombre(),
                cliente.obtener_correo(), cliente.obtener_telefono()))
        self.vaciar_tabla(self.tabla_servicios)
        for servicio in servicios:
            detalle = ""
            if isinstance(servicio, (ReservaHabitacion, ReservaSala)):
                detalle = f"Capacidad: {servicio.capacidad}"
            elif isinstance(servicio, AlquilerEquipos):
                detalle = f"Unidades: {servicio.unidades}"
            self.tabla_servicios.insert("", "end", values=(
                servicio.codigo, servicio.obtener_tipo(), servicio.nombre,
                detalle, formato_dinero(servicio.tarifa)))
        self.vaciar_tabla(self.tabla_reservas)
        for reserva in reservas:
            self.tabla_reservas.insert("", "end", values=(
                reserva.codigo, reserva.cliente.obtener_nombre(),
                reserva.servicio.nombre,
                f"{reserva.fecha_inicio} / {reserva.fecha_fin}",
                reserva.estado, formato_dinero(reserva.costo)))
        self.cmb_cliente["values"] = [
            f"{c.obtener_identificacion()} | {c.obtener_nombre()}" for c in clientes]
        self.cmb_servicio["values"] = [
            f"{s.codigo} | {s.obtener_tipo()} | {s.nombre}" for s in servicios]

    @staticmethod
    def vaciar_tabla(tabla):
        for elemento in tabla.get_children():
            tabla.delete(elemento)

    def ejecutar_pruebas_ui(self):
        resultados, aprobadas, total = ejecutar_pruebas()
        self.texto_pruebas.delete("1.0", "end")
        for nombre, correcto, detalle in resultados:
            marca = "[OK]" if correcto else "[FALLÓ]"
            self.texto_pruebas.insert("end", f"{marca} {nombre}\n    {detalle}\n\n")
        self.texto_pruebas.insert("end", f"RESULTADO: {aprobadas}/{total} pruebas aprobadas.\n")
        logger.info("Pruebas automáticas ejecutadas: %s/%s aprobadas", aprobadas, total)

    def mostrar_logs_ui(self):
        self.texto_logs.delete("1.0", "end")
        try:
            if ARCHIVO_LOG.exists():
                contenido = ARCHIVO_LOG.read_text(encoding="utf-8")
                self.texto_logs.insert("end", contenido[-20000:] or "El archivo de logs está vacío.")
            else:
                self.texto_logs.insert("end", "Todavía no se ha creado el archivo de logs.")
        except OSError as error:
            logger.exception("No fue posible leer el archivo de logs")
            self.texto_logs.insert("end", f"No se pudo leer el archivo: {error}")


def iniciar_aplicacion():
    """Inicia la ventana principal y registra fallos inesperados."""
    try:
        ventana = tk.Tk()
        AplicacionHotel(ventana)
        ventana.mainloop()
    except Exception as error:
        logger.exception("No fue posible iniciar la interfaz gráfica")
        try:
            messagebox.showerror("Error de inicio", str(error))
        except tk.TclError:
            print("No fue posible iniciar la interfaz gráfica:", error)


# ============================================================================
# 10. PUNTO DE ENTRADA DEL PROGRAMA
# ============================================================================

if __name__ == "__main__":
    print("=" * 58)
    print("                 SOFTWARE FJ HOTEL")
    print("       Sistema integral de gestión hotelera")
    print("=" * 58)
    print("1. Se cargará la interfaz gráfica de Tkinter.")
    print("2. En la pestaña Pruebas puede ejecutar 15 operaciones de validación.")
    print("3. Los registros de actividad se guardan en software_fj.log.")
    print("\nIniciando aplicación...")
    iniciar_aplicacion()
