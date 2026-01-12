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

# ================= TABLA RESPONSIVE =================
st.markdown('<div class="table-wrapper">', unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: grid; grid-template-columns: 1.2fr 1fr 1fr 1.2fr 0.8fr 0.8fr; gap: 6px; text-align: center; font-weight: bold;">
        <div>Día</div><div>Entrada</div><div>Salida real</div><div>Salida calculada</div><div>Tele</div><div>Vac</div>
    </div>
    """, unsafe_allow_html=True
)

for d in DIAS:
    # cada fila como grid
    entrada_val = st.session_state[d]["entrada"] if not st.session_state[d]["tele"] and not st.session_state[d]["vac"] else "—"
    salida_val = st.session_state[d]["salida"] if not st.session_state[d]["tele"] and not st.session_state[d]["vac"] else "—"

    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: 1.2fr 1fr 1fr 1.2fr 0.8fr 0.8fr; gap: 6px; text-align: center; margin-bottom: 4px;">
            <div>{d}</div>
            <div>{st.text_input('', entrada_val, key=f'ent_{d}', placeholder='08:30', label_visibility='collapsed') if not st.session_state[d]['tele'] and not st.session_state[d]['vac'] else '—'}</div>
            <div>{st.text_input('', salida_val, key=f'sal_{d}', placeholder='HH:MM', label_visibility='collapsed') if not st.session_state[d]['tele'] and not st.session_state[d]['vac'] else '—'}</div>
            <div id="calc_{d}"></div>
            <div>{st.checkbox('', key=f'tele_{d}', label_visibility='collapsed')}</div>
            <div>{st.checkbox('', key=f'vac_{d}', label_visibility='collapsed')}</div>
        </div>
        """, unsafe_allow_html=True
    )

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
