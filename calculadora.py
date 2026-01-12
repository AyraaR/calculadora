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

def calcular():
    horas_total = 0
    hoy = min(date.today().weekday(), 4)

    for dia in DIAS:
        d = st.session_state[dia]
        if d["vac"]:
            horas_total += HORAS_VACACIONES
        elif d["tele"]:
            horas_total += HORAS_TELETRABAJO
        elif d["entrada"] and d["salida"]:
            h1, h2 = h(d["entrada"]), h(d["salida"])
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
        and not st.session_state[d]["salida"]
    ]

    salidas = {}
    if pendientes:
        por_dia = horas_restantes / len(pendientes)

        for d in pendientes:
            entrada = st.session_state[d]["entrada"] or HORA_ENTRADA_DEFECTO
            salida = datetime.combine(date.today(), h(entrada).time()) + timedelta(minutes=int(por_dia * 60))

            if salida > datetime.combine(date.today(), h(HORA_COMIDA_DESDE).time()):
                salida += timedelta(minutes=PAUSA_COMIDA_MIN)

            if d == "Viernes":
                min_v = datetime.combine(date.today(), h(MIN_SALIDA_VIERNES).time())
                salida = min_v if st.session_state["viernes_1315"] else max(salida, min_v)
            else:
                salida = max(salida, datetime.combine(date.today(), h(MIN_SALIDA_LJ).time()))

            salidas[d] = salida.strftime("%H:%M")

    return horas_total, horas_restantes, salidas

# ================= UI =================
st.title("🕒 Calculadora de Salida")

# ---------------- HORAS SEMANALES ----------------
st.number_input("Horas semanales", min_value=0.0, step=0.5, key="horas_semanales")
st.checkbox("Salir a las 13:15 el viernes", key="viernes_1315")

st.divider()

# ---------------- ESTADO ----------------
for d in DIAS:
    if d not in st.session_state:
        st.session_state[d] = {"entrada": HORA_ENTRADA_DEFECTO, "salida": "", "tele": False, "vac": False}

# ---------------- DIAS ----------------
for d in DIAS:
    st.subheader(d)
    
    entrada_val = st.session_state[d]["entrada"] if not st.session_state[d]["tele"] and not st.session_state[d]["vac"] else "—"
    salida_val = st.session_state[d]["salida"] if st.session_state[d]["salida"] else ""

    if not st.session_state[d]["tele"] and not st.session_state[d]["vac"]:
        st.session_state[d]["entrada"] = st.text_input("Entrada", entrada_val, placeholder="08:30", key=f'ent_{d}')
        st.session_state[d]["salida"] = st.text_input(
            "Salida", salida_val, placeholder="HH:MM (editable)", key=f'sal_{d}'
        )
    else:
        st.markdown(f"<p>Entrada: —</p><p>Salida: —</p>", unsafe_allow_html=True)

    st.session_state[d]["tele"] = st.checkbox("Teletrabajo", key=f"tele_{d}")
    st.session_state[d]["vac"] = st.checkbox("Vacaciones", key=f"vac_{d}")

st.divider()

# ---------------- CALCULO ----------------
if st.button("Calcular"):
    horas_total, horas_restantes, salidas = calcular()

    # Actualizar salidas calculadas en session_state
    for d, h_calc in salidas.items():
        if not st.session_state[d]["salida"] or st.session_state[d]["salida"] == "":
            st.session_state[d]["salida"] = h_calc

    st.subheader("Resumen")
    st.write(f"Horas trabajadas: **{horas_total:.2f}**")
    st.write(f"Horas restantes: **{horas_restantes:.2f}**")

    st.subheader("Salidas recomendadas (editable)")
    for d in DIAS:
        st.write(f"{d}: **{st.session_state[d]['salida']}**")
