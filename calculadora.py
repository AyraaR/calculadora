import streamlit as st
from datetime import datetime, timedelta, date

# ================= CONFIG =================
st.set_page_config(
    page_title="Calculadora de Salida",
    page_icon="🕒",
    layout="centered"
)

# ================= CONSTANTES =================
HORA_ENTRADA_DEFECTO = "08:30"
MIN_SALIDA_LJ = "16:30"
MIN_SALIDA_VIERNES = "13:15"
HORAS_VACACIONES = 8
HORAS_TELETRABAJO = 9
HORAS_TELETRABAJO_VIERNES = 8
PAUSA_COMIDA_MIN = 30
HORA_COMIDA_DESDE = "16:00"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

# ================= FUNCIONES =================
def h(hora):
    return datetime.strptime(hora, "%H:%M")

def calcular_salidas(horas_semanales):
    hoy = min(date.today().weekday(), 4)
    horas_total = 0

    # Horas ya trabajadas
    for dia in DIAS:
        d = st.session_state[dia]
        if d["vac"]:
            horas_total += HORAS_VACACIONES
        elif d["tele"]:
            horas_total += HORAS_TELETRABAJO_VIERNES if dia == "Viernes" else HORAS_TELETRABAJO
        elif d["entrada"] and d["salida_real"]:
            h1, h2 = h(d["entrada"]), h(d["salida_real"])
            horas = (h2 - h1).seconds / 3600
            if h2 > h(HORA_COMIDA_DESDE):
                horas -= 0.5
            horas_total += horas

    horas_restantes = max(horas_semanales - horas_total, 0)

    pendientes = [
        dia for i, dia in enumerate(DIAS)
        if i >= hoy
        and not st.session_state[dia]["tele"]
        and not st.session_state[dia]["vac"]
        and not st.session_state[dia]["salida_real"]
    ]

    salidas = {}

    if not pendientes:
        return salidas, horas_total, horas_restantes

    horas_por_dia = horas_restantes / len(pendientes)

    for dia in pendientes:
        entrada = st.session_state[dia]["entrada"] or HORA_ENTRADA_DEFECTO
        salida = (
            datetime.combine(date.today(), h(entrada).time())
            + timedelta(minutes=int(horas_por_dia * 60))
        )

        if salida > datetime.combine(date.today(), h(HORA_COMIDA_DESDE).time()):
            salida += timedelta(minutes=PAUSA_COMIDA_MIN)

        if dia == "Viernes":
            min_v = datetime.combine(date.today(), h(MIN_SALIDA_VIERNES).time())
            salida = min_v if st.session_state["viernes_1315"] else max(salida, min_v)
        else:
            salida = max(
                salida,
                datetime.combine(date.today(), h(MIN_SALIDA_LJ).time())
            )

        salidas[dia] = salida.strftime("%H:%M")

    return salidas, horas_total, horas_restantes

# ================= UI =================
st.title("🕒 Calcula tu hora de salida")

horas_semanales = st.number_input(
    "Horas semanales",
    min_value=0.0,
    step=0.5
)

st.checkbox("Quiero salir a las 13:15 el viernes", key="viernes_1315")

st.divider()

# ================= ESTADO =================
for d in DIAS:
    if d not in st.session_state:
        st.session_state[d] = {
            "entrada": HORA_ENTRADA_DEFECTO,
            "salida_real": "",
            "tele": False,
            "vac": False,
        }

# ================= FORMULARIO =================
for d in DIAS:
    st.subheader(d)

    st.session_state[d]["tele"] = st.checkbox(
        "Teletrabajo", key=f"tele_{d}"
    )
    st.session_state[d]["vac"] = st.checkbox(
        "Vacaciones", key=f"vac_{d}"
    )

    if not st.session_state[d]["tele"] and not st.session_state[d]["vac"]:
        st.session_state[d]["entrada"] = st.text_input(
            "Hora de entrada",
            value=st.session_state[d]["entrada"],
            key=f"ent_{d}"
        )

        st.session_state[d]["salida_real"] = st.text_input(
            "Hora de salida real (opcional)",
            value=st.session_state[d]["salida_real"],
            placeholder="HH:MM",
            key=f"sal_{d}"
        )
    else:
        st.markdown("⛔ Día no laborable")

    st.divider()

# ================= RESULTADO =================
if st.button("Calcular hora de salida"):
    salidas, horas_total, horas_restantes = calcular_salidas(horas_semanales)

    st.success(f"Horas trabajadas: {horas_total:.2f}")
    st.success(f"Horas restantes: {horas_restantes:.2f}")

    st.divider()
    st.subheader("🧮 Horas de salida calculadas")

    if not salidas:
        st.info("No hay días pendientes de cálculo.")
    else:
        for dia, hora in salidas.items():
            st.markdown(f"**{dia}:** ⏰ `{hora}`")
