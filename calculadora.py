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
PAUSA_COMIDA_MIN = 30
HORA_COMIDA_DESDE = "16:00"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

# ================= FUNCIONES =================
def h(hora):
    return datetime.strptime(hora, "%H:%M")

def calcular_salidas():
    horas_total = 0
    hoy = min(date.today().weekday(), 4)

    # Horas ya computadas
    for dia in DIAS:
        d = st.session_state[dia]
        if d["vac"]:
            horas_total += HORAS_VACACIONES
        elif d["tele"]:
            horas_total += HORAS_TELETRABAJO
        elif d["entrada"] and d["salida_manual"]:
            h1, h2 = h(d["entrada"]), h(d["salida_manual"])
            horas = (h2 - h1).seconds / 3600
            if h2 > h(HORA_COMIDA_DESDE):
                horas -= 0.5
            horas_total += horas

    horas_restantes = max(st.session_state["horas_semanales"] - horas_total, 0)

    pendientes = [
        d for i, d in enumerate(DIAS)
        if i >= hoy
        and not st.session_state[d]["tele"]
        and not st.session_state[d]["vac"]
        and not st.session_state[d]["salida_manual"]
    ]

    salidas_calculadas = {}

    if not pendientes:
        return salidas_calculadas

    por_dia = horas_restantes / len(pendientes)

    for d in pendientes:
        entrada = st.session_state[d]["entrada"] or HORA_ENTRADA_DEFECTO
        salida = (
            datetime.combine(date.today(), h(entrada).time())
            + timedelta(minutes=int(por_dia * 60))
        )

        if salida > datetime.combine(date.today(), h(HORA_COMIDA_DESDE).time()):
            salida += timedelta(minutes=PAUSA_COMIDA_MIN)

        if d == "Viernes":
            min_v = datetime.combine(date.today(), h(MIN_SALIDA_VIERNES).time())
            salida = min_v if st.session_state["viernes_1315"] else max(salida, min_v)
        else:
            salida = max(
                salida,
                datetime.combine(date.today(), h(MIN_SALIDA_LJ).time())
            )

        salidas_calculadas[d] = salida.strftime("%H:%M")

    return salidas_calculadas

# ================= UI =================
st.title("🕒 Calculadora de Salida")

st.number_input(
    "Horas semanales",
    min_value=0.0,
    step=0.5,
    key="horas_semanales"
)

st.checkbox(
    "Salir a las 13:15 el viernes",
    key="viernes_1315"
)

st.divider()

# ================= ESTADO =================
for d in DIAS:
    if d not in st.session_state:
        st.session_state[d] = {
            "entrada": HORA_ENTRADA_DEFECTO,
            "salida_manual": "",
            "tele": False,
            "vac": False,
        }

if "salidas_calculadas" not in st.session_state:
    st.session_state["salidas_calculadas"] = {}

# ================= DIAS =================
for d in DIAS:
    st.subheader(d)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state[d]["tele"] = st.checkbox(
            "Teletrabajo",
            value=st.session_state[d]["tele"],
            key=f"tele_{d}"
        )
    with col2:
        st.session_state[d]["vac"] = st.checkbox(
            "Vacaciones",
            value=st.session_state[d]["vac"],
            key=f"vac_{d}"
        )

    if not st.session_state[d]["tele"] and not st.session_state[d]["vac"]:
        st.session_state[d]["entrada"] = st.text_input(
            "Entrada",
            value=st.session_state[d]["entrada"],
            key=f"ent_{d}"
        )

        st.session_state[d]["salida_manual"] = st.text_input(
            "Salida manual (opcional)",
            value=st.session_state[d]["salida_manual"],
            key=f"sal_manual_{d}",
            placeholder="HH:MM"
        )

        # 👇 AQUÍ SE MUESTRA LA CALCULADA
        salida_calc = st.session_state["salidas_calculadas"].get(d)
        if salida_calc:
            st.markdown(
                f"🧮 **Salida calculada:** `{salida_calc}`",
                unsafe_allow_html=True
            )
    else:
        st.markdown("Entrada: —")
        st.markdown("Salida: —")

st.divider()

# ================= CALCULO =================
if st.button("Calcular"):
    st.session_state["salidas_calculadas"] = calcular_salidas()
    st.success("Horas de salida calculadas ✅")
