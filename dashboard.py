import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go
import io
from sklearn.linear_model import LinearRegression
import numpy as np
import datetime as dt

st.set_page_config(page_title="Amazon FBA Inventory", layout="wide")

# --- СЛОВНИК ПЕРЕКЛАДІВ ---
translations = {
    "UA": {
        "title": "📦 Amazon FBA Ultimate BI",
        "update_btn": "🔄 Оновити дані",
        "sidebar_title": "🔍 Фільтри",
        "date_label": "📅 Дата:",
        "store_label": "🏪 Магазин:",
        "all_stores": "Всі",
        # НАЗВИ ВКЛАДОК
        "tab1": "📊 Головний Дашборд",
        "tab2": "📋 Таблица і Excel",
        "tab3": "📈 Історія та Тренди", # <-- ПОВЕРНУЛИ
        "tab4": "🧠 AI Прогноз (Beta)", # <-- ЗАЛИШИЛИ
        
        "summary": "Зведення за",
        "total_sku": "Всього SKU",
        "total_avail": "Всього Доступно",
        "total_inbound": "В дорозі (Inbound)",
        "total_reserved": "В резерві",
        "top_chart": "🏆 Top 15 товарів по залишках",
        "table_header": "📋 Повний список інвентарю",
        "download_excel": "📥 Завантажити Excel",
        
        # ТРЕНДИ (Tab 3)
        "chart_history": "📈 Загальна динаміка стоку (Всі товари)",
        "chart_sku": "🔍 Історія конкретного SKU",
        "select_sku": "Виберіть SKU:",
        
        # AI (Tab 4)
        "ai_header": "🧠 AI Прогноз залишків (Machine Learning)",
        "ai_select": "Оберіть SKU для прогнозу:",
        "ai_days": "На скільки днів прогнозувати?",
        "ai_result_date": "📅 Очікувана дата обнулення стоку:",
        "ai_result_days": "Днів до sold-out:",
        "ai_error": "Недостатньо даних для прогнозу (треба мінімум 3 дні історії)",
        "ai_ok": "✅ Запасів вистачить більше ніж на обраний період",

        "col_sku": "SKU",
        "col_name": "Назва товару",
        "col_avail": "Доступно",
        "col_inbound": "Їде (Inbound)",
        "col_reserved": "Резерв",
        "col_days": "Днів запасу",
        "footer_date": "📅 Останнє оновлення:"
    },
    "EN": {
        "title": "📦 Amazon FBA Ultimate BI",
        "update_btn": "🔄 Refresh Data",
        "sidebar_title": "🔍 Filters",
        "date_label": "📅 Date:",
        "store_label": "🏪 Store:",
        "all_stores": "All",
        "tab1": "📊 Main Dashboard",
        "tab2": "📋 Table & Excel",
        "tab3": "📈 History & Trends",
        "tab4": "🧠 AI Forecast (Beta)",
        
        "summary": "Summary for",
        "total_sku": "Total SKU",
        "total_avail": "Total Available",
        "total_inbound": "Total Inbound",
        "total_reserved": "Total Reserved",
        "top_chart": "🏆 Top 15 SKU by Availability",
        "table_header": "📋 Full Inventory List",
        "download_excel": "📥 Download Excel",
        
        "chart_history": "📈 Total Stock Dynamics",
        "chart_sku": "🔍 Specific SKU History",
        "select_sku": "Select SKU:",
        
        "ai_header": "🧠 AI Inventory Forecast (Machine Learning)",
        "ai_select": "Select SKU to forecast:",
        "ai_days": "Forecast horizon (days):",
        "ai_result_date": "📅 Expected Sold-out Date:",
        "ai_result_days": "Days until sold-out:",
        "ai_error": "Not enough data for forecast (need min 3 days history)",
        "ai_ok": "✅ Stock sufficient for selected period",

        "col_sku": "SKU",
        "col_name": "Product Name",
        "col_avail": "Available",
        "col_inbound": "Inbound",
        "col_reserved": "Reserved",
        "col_days": "Days of Supply",
        "footer_date": "📅 Last update:"
    },
    "RU": {
        "title": "📦 Amazon FBA Ultimate BI",
        "update_btn": "🔄 Обновить данные",
        "sidebar_title": "🔍 Фильтры",
        "date_label": "📅 Дата:",
        "store_label": "🏪 Магазин:",
        "all_stores": "Все",
        "tab1": "📊 Главный Дашборд",
        "tab2": "📋 Таблица и Excel",
        "tab3": "📈 История и Тренды",
        "tab4": "🧠 AI Прогноз (Beta)",
        
        "summary": "Сводка за",
        "total_sku": "Всего SKU",
        "total_avail": "Всего Доступно",
        "total_inbound": "В пути (Inbound)",
        "total_reserved": "В резерве",
        "top_chart": "🏆 Top 15 товаров по остаткам",
        "table_header": "📋 Полный список инвентаря",
        "download_excel": "📥 Скачать Excel",
        
        "chart_history": "📈 Общая динамика стока (Все товары)",
        "chart_sku": "🔍 История конкретного SKU",
        "select_sku": "Выберите SKU:",
        
        "ai_header": "🧠 AI Прогноз остатков (Machine Learning)",
        "ai_select": "Выберите SKU для прогноза:",
        "ai_days": "На сколько дней прогнозировать?",
        "ai_result_date": "📅 Ожидаемая дата обнуления:",
        "ai_result_days": "Дней до sold-out:",
        "ai_error": "Недостаточно данных для прогноза (нужно минимум 3 дня)",
        "ai_ok": "✅ Запасов хватит больше чем на выбранный период",

        "col_sku": "SKU",
        "col_name": "Название товара",
        "col_avail": "Доступно",
        "col_inbound": "В пути",
        "col_reserved": "Резерв",
        "col_days": "Дней запаса",
        "footer_date": "📅 Последнее обновление:"
    }
}

# --- ВИБІР МОВИ ---
lang_option = st.sidebar.selectbox("Language / Мова / Язык", ["UA 🇺🇦", "EN 🇺🇸", "RU 🌍"], index=0)
if "UA" in lang_option: lang = "UA"
elif "EN" in lang_option: lang = "EN"
else: lang = "RU"
t = translations[lang]

st.title(t["title"])

DATABASE_URL = os.getenv("DATABASE_URL")

@st.cache_data(ttl=60)
def load_data():
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM fba_inventory ORDER BY created_at DESC", conn)
    conn.close()
    return df

if st.button(t["update_btn"]):
    st.cache_data.clear()
    st.rerun()

df = load_data()

# --- ПІДГОТОВКА ДАНИХ ---
df['Available'] = pd.to_numeric(df['Available'], errors='coerce').fillna(0)
df['Inbound'] = pd.to_numeric(df['Inbound'], errors='coerce').fillna(0)
df['FBA Reserved Quantity'] = pd.to_numeric(df['FBA Reserved Quantity'], errors='coerce').fillna(0)
df['Total Quantity'] = pd.to_numeric(df['Total Quantity'], errors='coerce').fillna(0)
df['created_at'] = pd.to_datetime(df['created_at'])
df['date'] = df['created_at'].dt.date

# --- SIDEBAR ---
st.sidebar.header(t["sidebar_title"])
dates = sorted(df['date'].unique(), reverse=True)
selected_date = st.sidebar.selectbox(t["date_label"], dates, index=0)

previous_date = None
if len(dates) > 1:
    try:
        current_index = dates.index(selected_date)
        if current_index + 1 < len(dates):
            previous_date = dates[current_index + 1]
    except ValueError:
        pass

stores = [t["all_stores"]] + list(df['Store Name'].unique())
selected_store = st.sidebar.selectbox(t["store_label"], stores)

df_filtered = df[df['date'] == selected_date]
df_prev = df[df['date'] == previous_date] if previous_date else pd.DataFrame()

if selected_store != t["all_stores"]:
    df_filtered = df_filtered[df_filtered['Store Name'] == selected_store]
    if not df_prev.empty:
        df_prev = df_prev[df_prev['Store Name'] == selected_store]

# --- 4 TABS ---
tab1, tab2, tab3, tab4 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"]])

# === TAB 1: DASHBOARD ===
with tab1:
    st.subheader(f"{t['summary']} {selected_date}")
    curr_avail = int(df_filtered['Available'].sum())
    curr_inbound = int(df_filtered['Inbound'].sum())
    curr_reserved = int(df_filtered['FBA Reserved Quantity'].sum())
    
    delta_avail = (curr_avail - int(df_prev['Available'].sum())) if not df_prev.empty else 0
    delta_inbound = (curr_inbound - int(df_prev['Inbound'].sum())) if not df_prev.empty else 0
    delta_reserved = (curr_reserved - int(df_prev['FBA Reserved Quantity'].sum())) if not df_prev.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t["total_sku"], len(df_filtered))
    col2.metric(t["total_avail"], curr_avail, delta=delta_avail)
    col3.metric(t["total_inbound"], curr_inbound, delta=delta_inbound)
    col4.metric(t["total_reserved"], curr_reserved, delta=delta_reserved)

    st.markdown("---")
    st.subheader(t["top_chart"])
    top15 = df_filtered.nlargest(15, 'Available')
    fig_bar = px.bar(top15, x='Available', y='SKU', orientation='h', text='Available', title=t["top_chart"], color='Available', color_continuous_scale='Blues')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

# === TAB 2: TABLE ===
with tab2:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1: st.subheader(t["table_header"])
    with col_t2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_cols = ['SKU', 'ASIN', 'Product Name', 'Available', 'Inbound', 'FBA Reserved Quantity', 'Total Quantity', 'Days of Supply']
            final_export_cols = [c for c in export_cols if c in df_filtered.columns]
            df_filtered[final_export_cols].to_excel(writer, index=False, sheet_name='Inventory')
        buffer.seek(0)
        st.download_button(label=t["download_excel"], data=buffer, file_name=f"inventory_{selected_date}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def highlight_stock(val):
        if val == 0: return 'background-color: #ffcccc; color: black'
        elif val < 10: return 'background-color: #ffffcc; color: black'
        return ''

    display_map = {'SKU': t['col_sku'], 'Product Name': t['col_name'], 'Available': t['col_avail'], 'Inbound': t['col_inbound'], 'FBA Reserved Quantity': t['col_reserved'], 'Days of Supply': t['col_days'], 'ASIN': 'ASIN'}
    show_df = df_filtered.copy()
    existing_cols = [c for c in display_map.keys() if c in show_df.columns]
    show_df = show_df[existing_cols].rename(columns=display_map)
    st.dataframe(show_df.style.applymap(highlight_stock, subset=[t['col_avail']]), use_container_width=True, height=800)

# === TAB 3: HISTORY & TRENDS ===
with tab3:
    col_hist1, col_hist2 = st.columns([2, 1])
    
    with col_hist1:
        st.subheader(t["chart_history"])
        
        if selected_store != t["all_stores"]:
            df_history = df[df['Store Name'] == selected_store]
        else:
            df_history = df

        daily_totals = df_history.groupby('date').agg({
            'Available': 'sum',
            'Inbound': 'sum',
            'FBA Reserved Quantity': 'sum'
        }).reset_index().sort_values('date')

        rename_dict = {'Available': t['col_avail'], 'Inbound': t['col_inbound']}
        fig_line = px.line(daily_totals, x='date', y=['Available', 'Inbound'], markers=True, title=t["chart_history"])
        new_names = {k: v for k, v in rename_dict.items()}
        fig_line.for_each_trace(lambda tr: tr.update(name = new_names.get(tr.name, tr.name)))
        st.plotly_chart(fig_line, use_container_width=True)

    with col_hist2:
        st.subheader(t["chart_sku"])
        skus = sorted(df['SKU'].unique())
        selected_sku_hist = st.selectbox(t["select_sku"], skus, key="hist_select") # Унікальний ключ

        sku_history = df[df['SKU'] == selected_sku_hist][['date', 'Available', 'Inbound', 'Total Quantity']]
        sku_history = sku_history.groupby('date').first().reset_index().sort_values('date')

        if not sku_history.empty:
            st.metric(f"{t['col_avail']}", int(sku_history.iloc[-1]['Available']))
            fig_sku = px.area(sku_history, x='date', y='Available', title=f"{selected_sku_hist}")
            st.plotly_chart(fig_sku, use_container_width=True)
        else:
            st.info("No Data")

# === TAB 4: AI FORECAST ===
with tab4:
    st.subheader(t["ai_header"])
    
    skus = sorted(df['SKU'].unique())
    col_ai1, col_ai2 = st.columns([1, 1])
    with col_ai1:
        target_sku = st.selectbox(t["ai_select"], skus, key="ai_select") # Унікальний ключ
    with col_ai2:
        forecast_days = st.slider(t["ai_days"], 7, 90, 30)

    sku_data = df[df['SKU'] == target_sku].copy()
    sku_data = sku_data.sort_values('date')
    sku_data['date_ordinal'] = sku_data['created_at'].map(dt.datetime.toordinal)

    if len(sku_data) >= 3:
        X = sku_data[['date_ordinal']]
        y = sku_data['Available']

        model = LinearRegression()
        model.fit(X, y)

        last_date = sku_data['created_at'].max()
        future_dates = [last_date + dt.timedelta(days=x) for x in range(1, forecast_days + 1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)

        predictions = model.predict(future_ordinal)
        predictions = [max(0, int(p)) for p in predictions]
        
        df_forecast = pd.DataFrame({'date': future_dates, 'Predicted_Available': predictions, 'Type': 'Forecast'})

        sold_out_date = None
        days_left = None
        zero_stock = df_forecast[df_forecast['Predicted_Available'] == 0]
        if not zero_stock.empty:
            sold_out_date = zero_stock.iloc[0]['date'].date()
            days_left = (sold_out_date - dt.date.today()).days

        col_res1, col_res2 = st.columns(2)
        if sold_out_date:
            col_res1.error(f"{t['ai_result_date']} **{sold_out_date}**")
            col_res2.metric(t['ai_result_days'], f"{days_left} дн.")
        else:
            col_res1.success(t["ai_ok"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sku_data['date'], y=sku_data['Available'], mode='lines+markers', name='History', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df_forecast['date'], y=df_forecast['Predicted_Available'], mode='lines', name='AI Forecast', line=dict(color='red', dash='dash')))
        fig.update_layout(title=f"AI Forecast: {target_sku}", xaxis_title="Date", yaxis_title="Qty")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning(t["ai_error"])

st.sidebar.markdown("---")
st.sidebar.info(f"{t['footer_date']} {dates[0] if dates else '-'}")
