import streamlit as st
from datetime import datetime, timedelta, date

# ================== CONFIG ==================
st.set_page_config(
    page_title="Calculadora de Salida",
    page_icon="🕒",
    layout="wide"
)

# ================== CONSTANTES ==================
HORA_ENTRADA_DEFECTO = "08:30"
MIN_SALIDA_LJ = "16:30"
MIN_SALIDA_VIERNES = "13:15"
HORAS_VACACIONES = 8
HORAS_TELETRABAJO = 9
PAUSA_COMIDA_MIN = 30
HORA_COMIDA_DESDE = "16:00"

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

# ================== FUNCIONES ==================

def parse_hora(h):
    return datetime.strptime(h, "%H:%M")

def calcular():
    horas_total = 0

    # horas ya consolidadas
    for dia in DIAS:
        data = st.session_state[dia]

        if data["vac"]:
            horas_total += HORAS_VACACIONES

        elif data["tele"]:
            horas_total += HORAS_TELETRABAJO

        else:
            if data["entrada"] and data["salida"]:
                h1 = parse_hora(data["entrada"])
                h2 = parse_hora(data["salida"])
                horas = (h2 - h1).seconds / 3600

                if h2 > parse_hora(HORA_COMIDA_DESDE):
                    horas -= 0.5

                horas_total += horas

    horas_restantes = max(st.session_state["horas_semanales"] - horas_total, 0)

    # días pendientes
    hoy_index = min(date.today().weekday(), 4)
    pendientes = [
        dia for i, dia in enumerate(DIAS)
        if i >= hoy_index
        and not st.session_state[dia]["tele"]
        and not st.session_state[dia]["vac"]
        and not st.session_state[dia]["salida"]
    ]

    salidas_calculadas = {}

    if pendientes:
        horas_por_dia = horas_restantes / len(pendientes)

        for dia in pendientes:
            entrada = st.session_state[dia]["entrada"] or HORA_ENTRADA_DEFECTO
            h_ent = datetime.combine(date.today(), parse_hora(entrada).time())

            salida = h_ent + timedelta(minutes=int(horas_por_dia * 60))

            # comida solo si pasa de las 16:00
            if salida > datetime.combine(date.today(), parse_hora(HORA_COMIDA_DESDE).time()):
                salida += timedelta(minutes=PAUSA_COMIDA_MIN)

            # mínimos
            if dia == "Viernes":
                min_v = datetime.combine(date.today(), parse_hora(MIN_SALIDA_VIERNES).time())
                salida = min_v if st.session_state["viernes_1315"] else max(salida, min_v)
            else:
                min_lj = datetime.combine(date.today(), parse_hora(MIN_SALIDA_LJ).time())
                salida = max(salida, min_lj)

            salidas_calculadas[dia] = salida.strftime("%H:%M")

    return horas_total, horas_restantes, salidas_calculadas


# ================== UI ==================

st.title("🕒 Calculadora de salida de trabajo")

st.number_input(
    "Horas semanales",
    min_value=0.0,
    step=0.5,
    key="horas_semanales"
)

st.checkbox(
    "Quiero salir a las 13:15 el viernes",
    key="viernes_1315"
)

st.divider()

# inicializar estado por día
for dia in DIAS:
    if dia not in st.session_state:
        st.session_state[dia] = {
            "entrada": "",
            "salida": "",
            "tele": False,
            "vac": False
        }

# ================== TABLA ==================

cols = st.columns([1.2, 1.2, 1.2, 1.5, 1, 1])
cols[0].markdown("**Día**")
cols[1].markdown("**Entrada**")
cols[2].markdown("**Salida real**")
cols[3].markdown("**Salida calculada**")
cols[4].markdown("**Teletrabajo**")
cols[5].markdown("**Vacaciones**")

resultado = None

for dia in DIAS:
    c = st.columns([1.2, 1.2, 1.2, 1.5, 1, 1])

    c[0].write(dia)

    if st.session_state[dia]["tele"] or st.session_state[dia]["vac"]:
        c[1].write("—")
        c[2].write("—")
    else:
        st.session_state[dia]["entrada"] = c[1].text_input(
            "",
            value=st.session_state[dia]["entrada"],
            key=f"ent_{dia}",
            placeholder="08:30"
        )
        st.session_state[dia]["salida"] = c[2].text_input(
            "",
            value=st.session_state[dia]["salida"],
            key=f"sal_{dia}",
            placeholder="HH:MM"
        )

    c[4].checkbox("", key=f"tele_{dia}")
    c[5].checkbox("", key=f"vac_{dia}")

    st.session_state[dia]["tele"] = st.session_state[f"tele_{dia}"]
    st.session_state[dia]["vac"] = st.session_state[f"vac_{dia}"]

st.divider()

# ================== CÁLCULO ==================

if st.button("Calcular"):
    horas_total, horas_restantes, salidas = calcular()

    st.subheader("📊 Resumen")
    st.write(f"**Horas trabajadas:** {horas_total:.2f}")
    st.write(f"**Horas restantes:** {horas_restantes:.2f}")

    if salidas:
        st.subheader("🕓 Salidas calculadas")
        for d, h in salidas.items():
            st.write(f"**{d}:** {h}")
