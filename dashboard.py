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

st.set_page_config(page_title="Amazon FBA Ultimate BI", layout="wide", page_icon="📦")

# --- СЛОВНИК ПЕРЕКЛАДІВ ---
translations = {
    "UA": {
        "title": "📦 Amazon FBA: Business Intelligence Hub",
        "update_btn": "🔄 Оновити дані",
        "sidebar_title": "🔍 Фільтри",
        "date_label": "📅 Дата:",
        "store_label": "🏪 Магазин:",
        "all_stores": "Всі",
        
        "total_sku": "Всього SKU",
        "total_avail": "Штук на складі",
        "total_value": "💰 Вартість складу",
        "velocity_30": "Продажі (30 днів)",
        
        "chart_value_treemap": "💰 Де заморожені гроші?",
        "chart_velocity": "🚀 Швидкість vs Залишки",
        "chart_age": "⏳ Вік інвентарю",
        "top_money_sku": "🏆 Топ SKU за вартістю",
        "top_qty_sku": "🏆 Топ SKU за кількістю",
        "avg_price": "Середня ціна",
        
        "ai_header": "🧠 AI Прогноз залишків",
        "ai_select": "Оберіть SKU:",
        "ai_days": "Горизонт прогнозу:",
        "ai_result_date": "📅 Дата Sold-out:",
        "ai_result_days": "Днів залишилось:",
        "ai_ok": "✅ Запасів вистачить",
        "ai_error": "Недостатньо даних для прогнозу",
        
        "footer_date": "📅 Дані оновлено:",
        "download_excel": "📥 Завантажити Excel"
    },
    "EN": {
        "title": "📦 Amazon FBA: Business Intelligence Hub",
        "update_btn": "🔄 Refresh Data",
        "sidebar_title": "🔍 Filters",
        "date_label": "📅 Date:",
        "store_label": "🏪 Store:",
        "all_stores": "All",
        
        "total_sku": "Total SKU",
        "total_avail": "Total Units",
        "total_value": "💰 Inventory Value",
        "velocity_30": "Sales (30 days)",
        
        "chart_value_treemap": "💰 Where is the money?",
        "chart_velocity": "🚀 Velocity vs Stock",
        "chart_age": "⏳ Inventory Age",
        "top_money_sku": "🏆 Top SKU by Value",
        "top_qty_sku": "🏆 Top SKU by Quantity",
        "avg_price": "Avg Price",
        
        "ai_header": "🧠 AI Inventory Forecast",
        "ai_select": "Select SKU:",
        "ai_days": "Forecast Days:",
        "ai_result_date": "📅 Sold-out Date:",
        "ai_result_days": "Days left:",
        "ai_ok": "✅ Stock sufficient",
        "ai_error": "Not enough data",
        
        "footer_date": "📅 Last update:",
        "download_excel": "📥 Download Excel"
    },
    "RU": {
        "title": "📦 Amazon FBA: Business Intelligence Hub",
        "update_btn": "🔄 Обновить",
        "sidebar_title": "🔍 Фильтры",
        "date_label": "📅 Дата:",
        "store_label": "🏪 Магазин:",
        "all_stores": "Все",
        
        "total_sku": "Всего SKU",
        "total_avail": "Штук на складе",
        "total_value": "💰 Стоимость склада",
        "velocity_30": "Продажи (30 дней)",
        
        "chart_value_treemap": "💰 Где деньги?",
        "chart_velocity": "🚀 Скорость vs Остатки",
        "chart_age": "⏳ Возраст инвентаря",
        "top_money_sku": "🏆 Топ SKU по стоимости",
        "top_qty_sku": "🏆 Топ SKU по количеству",
        "avg_price": "Средняя цена",
        
        "ai_header": "🧠 AI Прогноз остатков",
        "ai_select": "Выберите SKU:",
        "ai_days": "Горизонт прогноза:",
        "ai_result_date": "📅 Дата Sold-out:",
        "ai_result_days": "Дней осталось:",
        "ai_ok": "✅ Запасов хватит",
        "ai_error": "Недостаточно данных",
        
        "footer_date": "📅 Данные обновлены:",
        "download_excel": "📥 Скачать Excel"
    }
}

DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================
# ФУНКЦІЇ ЗАВАНТАЖЕННЯ ДАНИХ
# ============================================

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        df = pd.read_sql("SELECT * FROM fba_inventory ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Помилка підключення до БД: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_orders():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        df = pd.read_sql("""
            SELECT * FROM orders 
            WHERE created_at = (SELECT MAX(created_at) FROM orders)
        """, conn)
        conn.close()
        
        df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
        df['Item Price'] = pd.to_numeric(df['Item Price'], errors='coerce').fillna(0)
        df['Item Tax'] = pd.to_numeric(df['Item Tax'], errors='coerce').fillna(0)
        df['Shipping Price'] = pd.to_numeric(df['Shipping Price'], errors='coerce').fillna(0)
        df['Total Price'] = df['Item Price'] + df['Item Tax'] + df['Shipping Price']
        
        return df
    except Exception as e:
        st.error(f"Помилка завантаження orders: {e}")
        return pd.DataFrame()

# ============================================
# REPORT FUNCTIONS
# ============================================

def show_overview(df_filtered, t, selected_date):
    """📊 Головний Дашборд з карточками звітів"""
    
    st.markdown("### 📊 Business Dashboard Overview")
    st.caption(f"Data snapshot: {selected_date}")
    
    # === KEY METRICS ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total SKU",
            value=len(df_filtered),
            delta=None
        )
    
    with col2:
        st.metric(
            label="📊 Units in Stock",
            value=f"{int(df_filtered['Available'].sum()):,}",
            delta=None
        )
    
    with col3:
        total_val = df_filtered['Stock Value'].sum()
        st.metric(
            label="💰 Inventory Value",
            value=f"${total_val:,.0f}",
            delta=None
        )
    
    with col4:
        velocity_sum = df_filtered['Velocity'].sum() * 30
        st.metric(
            label="📈 Sales (30 days)",
            value=f"{int(velocity_sum):,} units",
            delta=None
        )
    
    st.markdown("---")
    
    # === AVAILABLE REPORTS ===
    st.markdown("### 📂 Available Reports")
    st.caption("Click on any report card to view detailed analytics")
    
    # ROW 1: Main Reports
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("#### 🛒 Orders Analytics")
            st.markdown("""
            📈 Daily sales trends  
            🏆 Top performing SKU  
            💰 Revenue breakdown  
            📊 Order status tracking  
            """)
            if st.button("📊 View Orders Report →", key="btn_orders", use_container_width=True, type="primary"):
                st.session_state.report_choice = "🛒 Orders Analytics"
                st.rerun()
    
    with col2:
        with st.container(border=True):
            st.markdown("#### 💰 Finance (CFO Mode)")
            st.markdown("""
            💵 Total inventory value  
            🗺️ Money distribution map  
            📊 Top SKU by value  
            💸 Pricing analytics  
            """)
            if st.button("💰 View Finance Report →", key="btn_finance", use_container_width=True, type="primary"):
                st.session_state.report_choice = "💰 Finance (CFO Mode)"
                st.rerun()
    
    with col3:
        with st.container(border=True):
            st.markdown("#### 🐢 Inventory Health")
            st.markdown("""
            ⏳ Stock aging analysis  
            🚀 Sales velocity  
            📦 Distribution overview  
            ⚠️ Slow-moving items  
            """)
            if st.button("🐢 View Health Report →", key="btn_health", use_container_width=True, type="primary"):
                st.session_state.report_choice = "🐢 Inventory Health (Aging)"
                st.rerun()
    
    st.markdown("")
    
    # ROW 2: Additional Reports
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("#### 🧠 AI Forecast")
            st.markdown("""
            📅 Sold-out predictions  
            📉 Stock trend analysis  
            🤖 ML-based forecasting  
            ⏰ Optimal restock timing  
            """)
            if st.button("🧠 View AI Forecast →", key="btn_ai", use_container_width=True, type="primary"):
                st.session_state.report_choice = "🧠 AI Forecast"
                st.rerun()
    
    with col2:
        with st.container(border=True):
            st.markdown("#### 📋 Data Table")
            st.markdown("""
            📊 Full inventory list  
            🔍 Searchable dataset  
            📥 Excel export  
            📑 CSV download  
            """)
            if st.button("📋 View Data Table →", key="btn_table", use_container_width=True, type="primary"):
                st.session_state.report_choice = "📋 Data Table"
                st.rerun()
    
    with col3:
        with st.container(border=True):
            st.markdown("#### ↩️ Returns Analytics")
            st.markdown("""
            📦 Return reasons  
            💸 Cost analysis  
            🏆 Most returned SKU  
            📊 Return rate metrics  
            """)
            st.button("🚧 Coming Soon", key="btn_returns", disabled=True, use_container_width=True)
    
    st.markdown("---")
    
    # === QUICK CHART ===
    st.markdown("### 📊 Quick Overview: Top 15 SKU by Stock Level")
    
    if not df_filtered.empty:
        df_top = df_filtered.nlargest(15, 'Available')
        
        fig_bar = px.bar(
            df_top, 
            x='Available', 
            y='SKU', 
            orientation='h', 
            text='Available',
            color='Available',
            color_continuous_scale='Blues',
            labels={'Available': 'Units in Stock', 'SKU': ''}
        )
        fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending'},
            showlegend=False,
            height=500,
            xaxis_title="Units Available",
            yaxis_title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # === INFO FOOTER ===
    st.info("💡 **Tip**: Use the sidebar to navigate between reports or click on any card above for detailed analytics.")


def show_finance(df_filtered, t):
    """💰 Фінанси (CFO Mode)"""
    
    total_val = df_filtered['Stock Value'].sum()
    
    if total_val == 0:
        st.warning("⚠️ Увага: Ціна = 0. Запустіть оновлений amazon_etl.py!")
    
    # KPI
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Inventory Value", f"${total_val:,.2f}")
    
    with col2:
        avg_price = df_filtered[df_filtered['Price'] > 0]['Price'].mean()
        if pd.isna(avg_price): avg_price = 0
        st.metric(t["avg_price"], f"${avg_price:,.2f}")
    
    with col3:
        total_units = df_filtered['Available'].sum()
        avg_value_per_unit = total_val / total_units if total_units > 0 else 0
        st.metric("💵 Avg Value per Unit", f"${avg_value_per_unit:.2f}")
    
    st.markdown("---")
    
    # Treemap
    st.subheader(t["chart_value_treemap"])
    df_money = df_filtered[df_filtered['Stock Value'] > 0]
    
    if not df_money.empty:
        fig_tree = px.treemap(
            df_money, 
            path=['Store Name', 'SKU'], 
            values='Stock Value',
            color='Stock Value',
            hover_data=['Product Name', 'Available', 'Price'],
            color_continuous_scale='RdYlGn_r'
        )
        fig_tree.update_layout(height=600)
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("Немає даних про вартість товарів.")

    st.markdown("---")
    
    # Топ товарів
    st.subheader(t["top_money_sku"])
    
    df_top = df_filtered[['SKU', 'Product Name', 'Available', 'Price', 'Stock Value']].sort_values('Stock Value', ascending=False).head(10)
    
    st.dataframe(
        df_top.style.format({
            'Price': "${:.2f}", 
            'Stock Value': "${:,.2f}",
            'Available': "{:,.0f}"
        }),
        use_container_width=True,
        height=400
    )


def show_aging(df_filtered, t):
    """🐢 Здоров'я складу (Aging)"""
    
    total_val = df_filtered['Stock Value'].sum()
    age_cols = ['Upto 90 Days', '91 to 180 Days', '181 to 270 Days', '271 to 365 Days', 'More than 365 Days']
    valid_age_cols = [c for c in age_cols if c in df_filtered.columns]
    
    if valid_age_cols and df_filtered[valid_age_cols].sum().sum() > 0:
        age_sums = df_filtered[valid_age_cols].sum().reset_index()
        age_sums.columns = ['Age Group', 'Units']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(t["chart_age"])
            fig_pie = px.pie(
                age_sums, 
                values='Units', 
                names='Age Group', 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            st.subheader(t["chart_velocity"])
            fig_scatter = px.scatter(
                df_filtered, 
                x='Available', 
                y='Velocity', 
                size='Stock Value' if total_val > 0 else 'Available',
                color='Store Name',
                hover_name='SKU',
                hover_data=['Product Name', 'Available', 'Velocity'],
                log_x=True
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Дані про вік інвентарю відсутні. Перевірте звіт AGED у ETL.")


def show_ai_forecast(df, t):
    """🧠 AI Прогноз"""
    
    st.markdown("### Select SKU for Forecast")
    
    skus = sorted(df['SKU'].unique())
    if skus:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            target_sku = st.selectbox(t["ai_select"], skus, key="forecast_sku")
        
        with col2:
            forecast_days = st.slider(t["ai_days"], 7, 90, 30)

        sku_data = df[df['SKU'] == target_sku].copy().sort_values('date')
        sku_data['date_ordinal'] = sku_data['created_at'].map(dt.datetime.toordinal)

        if len(sku_data) >= 3:
            X = sku_data[['date_ordinal']]
            y = sku_data['Available']
            model = LinearRegression()
            model.fit(X, y)
            
            last_date = sku_data['created_at'].max()
            future_dates = [last_date + dt.timedelta(days=x) for x in range(1, forecast_days + 1)]
            future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
            predictions = [max(0, int(p)) for p in model.predict(future_ordinal)]
            
            df_forecast = pd.DataFrame({'date': future_dates, 'Predicted': predictions})
            
            sold_out = df_forecast[df_forecast['Predicted'] == 0]
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            if not sold_out.empty:
                s_date = sold_out.iloc[0]['date'].date()
                days_left = (s_date - dt.date.today()).days
                
                with col1:
                    st.error(f"### {t['ai_result_date']}")
                    st.markdown(f"# **{s_date}**")
                
                with col2:
                    st.metric(
                        label=t['ai_result_days'],
                        value=f"{days_left} days",
                        delta=f"-{forecast_days - days_left} from forecast"
                    )
            else:
                with col1:
                    st.success(f"### {t['ai_ok']}")
                    st.markdown(f"Stock will last **{forecast_days}+ days**")

            st.markdown("---")
            st.subheader("📊 Forecast Chart")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=sku_data['date'], 
                y=sku_data['Available'], 
                mode='lines+markers', 
                name='Historical Data',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_forecast['date'], 
                y=df_forecast['Predicted'], 
                mode='lines', 
                name='AI Forecast',
                line=dict(dash='dash', color='red', width=2)
            ))
            
            fig.update_layout(
                height=500,
                hovermode='x unified',
                xaxis_title="Date",
                yaxis_title="Units Available"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(t["ai_error"])
    else:
        st.info("Немає SKU для аналізу")


def show_data_table(df_filtered, t, selected_date):
    """📋 Таблиця даних"""
    
    st.markdown("### 📊 Complete Inventory Dataset")
    st.caption(f"Total records: {len(df_filtered):,}")
    
    # Export buttons
    col1, col2 = st.columns([1, 4])
    
    with col1:
        buffer = io.BytesIO()
        df_excel = df_filtered.copy().fillna('')
        
        for col in df_excel.select_dtypes(include=['object']).columns:
            df_excel[col] = df_excel[col].astype(str).str[:32000]
        
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_excel.to_excel(writer, index=False, sheet_name='Inventory')
            buffer.seek(0)
            
            st.download_button(
                label=t["download_excel"],
                data=buffer,
                file_name=f"inventory_{selected_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"inventory_{selected_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Data Table
    st.dataframe(
        df_filtered,
        use_container_width=True,
        height=600
    )


def show_orders():
    """🛒 Замовлення"""
    
    df_orders = load_orders()
    
    if df_orders.empty:
        st.warning("⚠️ Дані відсутні. Запустіть amazon_orders_loader.py")
        return
    
    # Фільтр по датам
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛒 Orders Filters")
    
    min_date = df_orders['Order Date'].min().date()
    max_date = df_orders['Order Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "📅 Date Range:",
        value=(max_date - dt.timedelta(days=7), max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_orders_filtered = df_orders[
            (df_orders['Order Date'].dt.date >= start_date) &
            (df_orders['Order Date'].dt.date <= end_date)
        ]
    else:
        df_orders_filtered = df_orders
    
    # KPI
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_orders = df_orders_filtered['Order ID'].nunique()
    total_items = df_orders_filtered['Quantity'].sum()
    total_revenue = df_orders_filtered['Total Price'].sum()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    col1.metric("📦 Total Orders", f"{total_orders:,}")
    col2.metric("📦 Total Items", f"{int(total_items):,}")
    col3.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    col4.metric("💵 Avg Order Value", f"${avg_order_value:.2f}")
    
    st.markdown("---")
    
    # ГРАФІКИ
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Orders per Day")
        
        orders_per_day = df_orders_filtered.groupby(
            df_orders_filtered['Order Date'].dt.date
        ).agg({
            'Order ID': 'nunique',
            'Total Price': 'sum'
        }).reset_index()
        orders_per_day.columns = ['Date', 'Orders', 'Revenue']
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=orders_per_day['Date'],
            y=orders_per_day['Orders'],
            mode='lines+markers',
            name='Orders',
            line=dict(color='blue', width=2),
            fill='tozeroy'
        ))
        fig_trend.update_layout(
            xaxis_title="Date",
            yaxis_title="Orders",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Revenue per Day")
        
        fig_revenue = go.Figure()
        fig_revenue.add_trace(go.Bar(
            x=orders_per_day['Date'],
            y=orders_per_day['Revenue'],
            name='Revenue',
            marker_color='green'
        ))
        fig_revenue.update_layout(
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    st.markdown("---")
    
    # TOP SKU
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top 10 SKU by Orders")
        
        top_sku_orders = df_orders_filtered.groupby('SKU').agg({
            'Order ID': 'count',
            'Quantity': 'sum'
        }).reset_index()
        top_sku_orders.columns = ['SKU', 'Order Count', 'Quantity']
        top_sku_orders = top_sku_orders.sort_values('Order Count', ascending=False).head(10)
        
        fig_top = px.bar(
            top_sku_orders,
            x='Order Count',
            y='SKU',
            orientation='h',
            text='Order Count',
            color='Order Count',
            color_continuous_scale='Blues'
        )
        fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Top 10 SKU by Revenue")
        
        top_sku_revenue = df_orders_filtered.groupby('SKU').agg({
            'Total Price': 'sum'
        }).reset_index()
        top_sku_revenue.columns = ['SKU', 'Revenue']
        top_sku_revenue = top_sku_revenue.sort_values('Revenue', ascending=False).head(10)
        
        fig_rev = px.bar(
            top_sku_revenue,
            x='Revenue',
            y='SKU',
            orientation='h',
            text='Revenue',
            color='Revenue',
            color_continuous_scale='Greens'
        )
        fig_rev.update_traces(texttemplate='$%{text:.0f}')
        fig_rev.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
        st.plotly_chart(fig_rev, use_container_width=True)
    
    st.markdown("---")
    
    # STATUS PIE
    st.markdown("#### 📊 Orders by Status")
    
    status_counts = df_orders_filtered.groupby('Order Status').agg({
        'Order ID': 'nunique'
    }).reset_index()
    status_counts.columns = ['Status', 'Orders']
    
    fig_status = px.pie(
        status_counts,
        values='Orders',
        names='Status',
        hole=0.4
    )
    fig_status.update_layout(height=400)
    st.plotly_chart(fig_status, use_container_width=True)
    
    st.markdown("---")
    
    # TABLE
    st.markdown("#### 📋 Orders Details")
    
    unique_skus = ['All'] + sorted(df_orders_filtered['SKU'].unique().tolist())
    selected_sku = st.selectbox("Filter by SKU:", unique_skus)
    
    df_display = df_orders_filtered if selected_sku == 'All' else df_orders_filtered[df_orders_filtered['SKU'] == selected_sku]
    
    display_cols = [
        'Order Date', 'Order ID', 'SKU', 'Product Name',
        'Quantity', 'Item Price', 'Total Price', 'Order Status',
        'Fulfillment Channel', 'Ship City', 'Ship State'
    ]
    
    df_show = df_display[display_cols].sort_values('Order Date', ascending=False)
    
    st.dataframe(
        df_show.style.format({
            'Item Price': '${:.2f}',
            'Total Price': '${:.2f}',
            'Quantity': '{:.0f}'
        }),
        use_container_width=True,
        height=400
    )
    
    # Export
    buffer = io.BytesIO()
    df_excel = df_show.copy()
    
    if 'Order Date' in df_excel.columns:
        df_excel['Order Date'] = df_excel['Order Date'].astype(str).replace('NaT', '')
    
    df_excel = df_excel.fillna('')
    
    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Orders')
        buffer.seek(0)
        
        st.download_button(
            label="📥 Download Orders Excel",
            data=buffer,
            file_name=f"orders_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except:
        pass


# ============================================
# MAIN APP
# ============================================

# Session state
if 'report_choice' not in st.session_state:
    st.session_state.report_choice = "🏠 Overview"

# Мова
lang_option = st.sidebar.selectbox("🌍 Language", ["UA 🇺🇦", "EN 🇺🇸", "RU 🌍"], index=0)
if "UA" in lang_option: lang = "UA"
elif "EN" in lang_option: lang = "EN"
else: lang = "RU"
t = translations[lang]

# Refresh button
if st.sidebar.button(t["update_btn"], use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Завантаження
df = load_data()

if df.empty:
    st.error("❌ База даних порожня. Запустіть amazon_fba_inventory_loader.py")
    st.stop()

# Обробка даних
if 'Price' not in df.columns:
    df['Price'] = 0.0

numeric_cols = ['Available', 'Inbound', 'FBA Reserved Quantity', 'Total Quantity', 'Price', 'Velocity', 
                'Upto 90 Days', '91 to 180 Days', '181 to 270 Days', '271 to 365 Days', 'More than 365 Days']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    else:
        df[col] = 0

df['Stock Value'] = df['Available'] * df['Price']
df['created_at'] = pd.to_datetime(df['created_at'])
df['date'] = df['created_at'].dt.date

# ФІЛЬТРИ
st.sidebar.header(t["sidebar_title"])

dates = sorted(df['date'].unique(), reverse=True)
if dates:
    selected_date = st.sidebar.selectbox(t["date_label"], dates, index=0)
else:
    selected_date = None

stores = [t["all_stores"]] + list(df['Store Name'].unique())
selected_store = st.sidebar.selectbox(t["store_label"], stores)

# Фільтрація
if selected_date:
    df_filtered = df[df['date'] == selected_date]
else:
    df_filtered = df

if selected_store != t["all_stores"]:
    df_filtered = df_filtered[df_filtered['Store Name'] == selected_store]

# НАВІГАЦІЯ
st.sidebar.markdown("---")
st.sidebar.header("📊 Reports")

report_choice = st.sidebar.radio(
    "Select Report:",
    [
        "🏠 Overview",
        "💰 Finance (CFO Mode)",
        "🐢 Inventory Health (Aging)",
        "🧠 AI Forecast",
        "📋 Data Table",
        "🛒 Orders Analytics"
    ],
    index=[
        "🏠 Overview",
        "💰 Finance (CFO Mode)",
        "🐢 Inventory Health (Aging)",
        "🧠 AI Forecast",
        "📋 Data Table",
        "🛒 Orders Analytics"
    ].index(st.session_state.report_choice) if st.session_state.report_choice in [
        "🏠 Overview",
        "💰 Finance (CFO Mode)",
        "🐢 Inventory Health (Aging)",
        "🧠 AI Forecast",
        "📋 Data Table",
        "🛒 Orders Analytics"
    ] else 0
)

st.session_state.report_choice = report_choice

# ДИНАМІЧНИЙ ЗАГОЛОВОК
report_titles = {
    "🏠 Overview": "📦 Amazon FBA: Business Intelligence Hub",
    "💰 Finance (CFO Mode)": "💰 Finance (CFO Mode)",
    "🐢 Inventory Health (Aging)": "🐢 Inventory Health (Aging)",
    "🧠 AI Forecast": "🧠 AI Forecast",
    "📋 Data Table": "📋 Data Table",
    "🛒 Orders Analytics": "🛒 Orders Analytics"
}

st.title(report_titles[report_choice])

# ВІДОБРАЖЕННЯ ЗВІТУ
if df_filtered.empty and report_choice != "🛒 Orders Analytics":
    st.info("Дані відсутні за вибраними фільтрами.")
else:
    if report_choice == "🏠 Overview":
        show_overview(df_filtered, t, selected_date)
    elif report_choice == "💰 Finance (CFO Mode)":
        show_finance(df_filtered, t)
    elif report_choice == "🐢 Inventory Health (Aging)":
        show_aging(df_filtered, t)
    elif report_choice == "🧠 AI Forecast":
        show_ai_forecast(df, t)
    elif report_choice == "📋 Data Table":
        show_data_table(df_filtered, t, selected_date)
    elif report_choice == "🛒 Orders Analytics":
        show_orders()

# Footer
st.sidebar.markdown("---")
if dates:
    st.sidebar.info(f"{t['footer_date']} {dates[0]}")

st.sidebar.markdown("---")
st.sidebar.caption("📦 Amazon FBA BI System v2.0")
st.sidebar.caption("Built with ❤️ using Streamlit")
