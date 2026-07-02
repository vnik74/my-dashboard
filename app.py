pythonimport streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import urllib.request
from io import StringIO

# 1. НАСТРОЙКА ИНТЕРФЕЙСА ДАШБОРДА
st.set_page_config(page_title="Аналитика продаж РФ", layout="wide")
st.title("📊 Автономный интерактивный дашборд анализа продаж")

# ==========================================
# 2. ВСЕ ТАБЛИЦЫ ВНУТРИ КОДА (ДАННЫЕ И СПРАВОЧНИКИ)
# ==========================================

# Таблица 1: Тразакции (Факт)
fact_data = """ID Заказа	Дата	Регион	Менеджер	Клиент	Тип клиента	Канал продаж	Товар	Категория	Кол-во	Цена, ₽	Скидка, %	Себестоимость ед., ₽	Доставка, ₽	Статус
1001	01.06.2026	Центральный федеральный округ	Иванов А.	ООО Вектор	B2B	Прямые продажи	Ноутбук	Электроника	2	70000	0.05	50000	1500	Оплачен
1002	03.06.2026	Северо-Западный федеральный округ	Петров П.	ИП Сидоров	B2B	Сайт	Кресло	Мебель	5	12000	0.00	8000	3000	Доставлен
1003	05.06.2026	Приволжский федеральный округ	Сидорова Е.	АО Спектр	B2B	Прямые продажи	Смартфон	Электроника	3	45000	0.10	32000	1200	В пути
1004	07.06.2026	Центральный федеральный округ	Иванов А.	Физическое лицо	B2C	Маркетплейс	Стол	Мебель	1	25000	0.00	15000	800	Оплачен
1005	10.06.2026	Северо-Западный федеральный округ	Петров П.	ООО Вектор	B2B	Прямые продажи	Монитор	Электроника	4	20000	0.05	14000	2000	Отменен
1006	12.06.2026	Приволжский федеральный округ	Сидорова Е.	Физическое лицо	B2C	Сайт	Стул	Мебель	10	5000	0.03	3000	4000	Доставлен
1007	15.06.2026	Центральный федеральный округ	Кузнецов Д.	АО Спектр	B2B	Прямые продажи	Ноутбук	Электроника	1	70000	0.00	50000	1500	Оплачен
1008	18.06.2026	Северо-Западный федеральный округ	Петров П.	Физическое лицо	B2C	Маркетплейс	Принтер	Электроника	2	15000	0.07	11000	600	В пути
1009	20.06.2026	Приволжский федеральный округ	Сидорова Е.	ООО Вектор	B2B	Сайт	Шкаф	Мебель	1	40000	0.00	25000	2500	Доставлен
1010	22.06.2026	Центральный федеральный округ	Иванов А.	АО Спектр	B2B	Прямые продажи	Мышь	Электроника	15	2000	0.10	1200	1000	Оплачен
1011	25.06.2026	Северо-Западный федеральный округ	Кузнецов Д.	ИП Сидоров	B2B	Сайт	Стол	Мебель	2	25000	0.05	15000	1800	Оплачен
1012	27.06.2026	Приволжский федеральный округ	Сидорова Е.	Физическое лицо	B2C	Маркетплейс	Смартфон	Электроника	2	45000	0.00	32000	1100	Новый"""

# Таблица 2: Планы продаж
plans_data = """Менеджер	План Выручка, ₽	План Чистая Прибыль, ₽
Иванов А.	200000	50000
Петров П.	180000	45000
Сидорова Е.	300000	75000
Кузнецов Д.	150000	35000"""

# Таблица 4: Справочник Менеджеров
managers_data = """ФИО	Отдел	Грейд
Иванов А.	B2B Продажи	Senior
Петров П.	Региональные продажи	Middle
Сидорова Е.	B2C Департамент	Senior
Кузнецов Д.	B2B Продажи	Junior"""

# Чтение текстовых строк напрямую в память через StringIO
df_fact = pd.read_csv(StringIO(fact_data), sep="\t")
df_plans = pd.read_csv(StringIO(plans_data), sep="\t")
df_managers = pd.read_csv(StringIO(managers_data), sep="\t")

# Загрузка карты округов России (GeoJSON)
@st.cache_data
def load_geojson():
    url = "https://githubusercontent.com"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

geojson_ru = load_geojson()

# ==========================================
# 3. ПРЕОБРАЗОВАНИЕ, ОЧИСТКА И ОБЪЕДИНЕНИЕ СЛОВАРЕЙ
# ==========================================

# Генерация Справочника Календаря (Таблица 3) на лету по датам из транзакций
df_fact['Дата'] = pd.to_datetime(df_fact['Дата'], format='%d.%m.%Y')
df_fact['День недели'] = df_fact['Дата'].dt.strftime('%A')
df_fact['Месяц'] = df_fact['Дата'].dt.strftime('%B %Y')

# Вычисление расчетных показателей (Выручка нетто, себестоимость, маржа)
df_fact['Выручка Гросс'] = df_fact['Кол-во'] * df_fact['Цена, ₽']
df_fact['Сумма скидки'] = df_fact['Выручка Гросс'] * df_fact['Скидка, %']
df_fact['Выручка Нетто'] = df_fact['Выручка Гросс'] - df_fact['Сумма скидки']
df_fact['Себестоимость всего'] = df_fact['Кол-во'] * df_fact['Себестоимость ед., ₽']
df_fact['Чистая Прибыль'] = df_fact['Выручка Нетто'] - df_fact['Себестоимость всего'] - df_fact['Доставка, ₽']

# Обогащение транзакций данными из справочника сотрудников (Аналог JOIN / ВПР)
df_fact = df_fact.merge(df_managers, left_on='Менеджер', right_on='ФИО', how='left')

# ==========================================
# 4. БЛОК ИНТЕРАКТИВНЫХ ФИЛЬТРОВ И АНОМАЛИЙ
# ==========================================

st.sidebar.header("⚙️ Панель управления")

# Выявление аномалий: Исключение отмененных заказов
exclude_canceled = st.sidebar.checkbox("Очистить данные (Исключить отмененные)", value=True)
if exclude_canceled:
    df_fact = df_fact[df_fact['Статус'] != 'Отменен']

# Срезы / Интерактивные фильтры
regions = st.sidebar.multiselect("Фильтр по Регионам", options=df_fact['Регион'].unique(), default=df_fact['Регион'].unique())
categories = st.sidebar.multiselect("Фильтр по Категориям", options=df_fact['Категория'].unique(), default=df_fact['Категория'].unique())

# Применение интерактивной фильтрации
df_filtered = df_fact[(df_fact['Регион'].isin(regions)) & (df_fact['Категория'].isin(categories))]

# ==========================================
# 5. КАРТОЧКИ KPI
# ==========================================

total_rev = df_filtered['Выручка Нетто'].sum()
total_prof = df_filtered['Чистая Прибыль'].sum()
avg_margin = (total_prof / total_rev * 100) if total_rev > 0 else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Выручка (Нетто)", value=f"{total_rev:,.0f} ₽".replace(",", " "))
kpi2.metric(label="Чистая Прибыль", value=f"{total_prof:,.0f} ₽".replace(",", " "))
kpi3.metric(label="Рентабельность (Маржа)", value=f"{avg_margin:.1f}%")

st.markdown("---")

# ==========================================
# 6. КАРТА РФ И СВОДНЫЕ ГРАФИКИ
# ==========================================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🗺️ Географический анализ прибыли по округам")
    df_map = df_filtered.groupby('Регион')['Чистая Прибыль'].sum().reset_index()
    
    fig_map = px.choropleth(
        df_map, geojson=geojson_ru, locations="Регион", 
        featureidkey="properties.name", color="Чистая Прибыль",
        color_continuous_scale="YlOrRd", labels={'Чистая Прибыль':'Прибыль, ₽'}
    )
    fig_map.update_geos(showland=True, landcolor="lightgray", fitbounds="locations")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=400)
    st.plotly_chart(fig_map, use_container_width=True)

with col_right:
    st.subheader("📈 Динамика продаж по датам транзакций")
    df_trend = df_filtered.groupby('Дата')['Выручка Нетто'].sum().reset_index()
    fig_trend = px.line(df_trend, x='Дата', y='Выручка Нетто', markers=True, template="plotly_white")
    fig_trend.update_traces(line_color="crimson")
    fig_trend.update_layout(height=400, margin={"t":20})
    st.plotly_chart(fig_trend, use_container_width=True)

# ПЛАН-ФАКТ АНАЛИЗ С ОТОБРАЖЕНИЕМ ГРЕЙДОВ СОТРУДНИКОВ
st.markdown("---")
st.subheader("👥 Анализ эффективности сотрудников (План vs Факт)")

df_emp_fact = df_filtered.groupby(['Менеджер', 'Грейд'])['Выручка Нетто'].sum().reset_index()
df_perf = df_plans.merge(df_emp_fact, on='Менеджер', how='left').fillna(0)
df_perf['% Выполнения'] = (df_perf['Выручка Нетто'] / df_perf['План Выручка, ₽']) * 100

fig_perf = go.Figure()
fig_perf.add_trace(go.Bar(x=df_perf['Менеджер'], y=df_perf['План Выручка, ₽'], name='План продаж', marker_color='gainsboro'))
fig_perf.add_trace(go.Bar(x=df_perf['Менеджер'], y=df_perf['Выручка Нетто'], name='Факт продаж', marker_color='teal'))
fig_perf.update_layout(barmode='group', template="plotly_white", height=350)
st.plotly_chart(fig_perf, use_container_width=True)

# Интерактивная таблица для менеджеров
st.dataframe(
    df_perf[['Менеджер', 'Грейд', 'План Выручка, ₽', 'Выручка Нетто', '% Выполнения']]
    .style.format({'% Выполнения': '{:.1f}%', 'План Выручка, ₽': '{:,.0f}', 'Выручка Нетто': '{:,.0f}'})
)
