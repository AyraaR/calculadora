import streamlit as st
from datetime import datetime, timedelta, date

# ================= CONFIG =================
st.set_page_config(
    page_title="Calculadora de Salida",
    page_icon="🕒",
    layout="centered"
)

# ================= CSS DESKTOP-LIKE =================
st.markdown("""
<style>
    .block-container {
        max-width: 1100px;
        padding-top: 1rem;
    }

    /* Tabla con scroll horizontal */
    .table-wrapper {
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
    }

    .table {
        min-width: 900px;
    }

    .table th, .table td {
        padding: 6px 8px;
        text-align: center;
        font-size: 0.85rem;
        white-space: nowrap;
    }

    input {
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

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
def h(h):
    return datetime.strptime(h, "%H:%M")

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
st.title("🕒 Calculadora de salida")

st.number_input("Horas semanales", min_value=0.0, step=0.5, key="horas_semanales")
st.checkbox("Salir a las 13:15 el viernes", key="viernes_1315")

st.divider()

# inicializar estado
for d in DIAS:
    if d not in st.session_state:
        st.session_state[d] = {"entrada": "", "salida": "", "tele": False, "vac": False}

# =================== TABLA MOBILE-FIRST ===================
st.markdown("""
<style>
.scroll-container {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    gap: 16px;
    padding-bottom: 8px;
}

.day-card {
    flex: 0 0 90%; /* cada "día" ocupa 90% del ancho del contenedor */
    scroll-snap-align: start;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    background-color: #f9f9f9;
    min-width: 250px;
}

.day-card h4 {
    text-align: center;
    margin-bottom: 8px;
}

.day-card input[type="text"] {
    width: 100%;
    padding: 6px;
    margin-bottom: 6px;
    font-size: 0.9rem;
}

.day-card label {
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="scroll-container">', unsafe_allow_html=True)

for d in DIAS:
    entrada_val = st.session_state[d]["entrada"] if not st.session_state[d]["tele"] and not st.session_state[d]["vac"] else "—"
    salida_val = st.session_state[d]["salida"] if not st.session_state[d]["tele"] and not st.session_state[d]["vac"] else "—"

    st.markdown(f'<div class="day-card">', unsafe_allow_html=True)
    st.markdown(f'<h4>{d}</h4>', unsafe_allow_html=True)

    if not st.session_state[d]["tele"] and not st.session_state[d]["vac"]:
        st.session_state[d]["entrada"] = st.text_input("Entrada", entrada_val, placeholder="08:30", key=f'ent_{d}')
        st.session_state[d]["salida"] = st.text_input("Salida", salida_val, placeholder="HH:MM", key=f'sal_{d}')
    else:
        st.markdown(f'<p>Entrada: —</p><p>Salida: —</p>', unsafe_allow_html=True)

    st.session_state[d]["tele"] = st.checkbox("Teletrabajo", key=f"tele_{d}")
    st.session_state[d]["vac"] = st.checkbox("Vacaciones", key=f"vac_{d}")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ================= CALCULO =================
if st.button("Calcular"):
    horas_total, horas_restantes, salidas = calcular()

    st.subheader("Resumen")
    st.write(f"Horas trabajadas: **{horas_total:.2f}**")
    st.write(f"Horas restantes: **{horas_restantes:.2f}**")

    if salidas:
        st.subheader("Salidas recomendadas")
        for d, h in salidas.items():
            st.write(f"{d}: **{h}**")
