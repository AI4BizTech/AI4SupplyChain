"""
Demand forecasting page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def render_forecasting_page():
    """Render the demand forecasting page"""
    st.title("📈 Demand Forecasting")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Forecasting Actions")
        action = st.selectbox(
            "Choose Action",
            ["Generate Forecast", "Forecast Accuracy", "Bulk Forecasting", "Seasonal Analysis"]
        )
    
    try:
        from src.services.forecasting import ForecastingService
        from src.services.inventory import InventoryService
        
        forecasting_service = ForecastingService()
        inventory_service = InventoryService()
        
        if action == "Generate Forecast":
            show_generate_forecast(forecasting_service, inventory_service)
        elif action == "Forecast Accuracy":
            show_forecast_accuracy(forecasting_service, inventory_service)
        elif action == "Bulk Forecasting":
            show_bulk_forecasting(forecasting_service, inventory_service)
        elif action == "Seasonal Analysis":
            show_seasonal_analysis(forecasting_service, inventory_service)
            
    except Exception as e:
        st.error(f"Error loading demand forecasting: {e}")
        st.info("Please ensure the database is initialized and services are available.")

def show_generate_forecast(forecasting_service, inventory_service):
    """Show single product forecast generation"""
    st.header("🔮 Generate Demand Forecast")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product selection
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Select Product", product_options)
            
            if selected_product:
                sku = selected_product.split(" - ")[0]
                product = inventory_service.get_product_by_sku(sku)
        except:
            st.error("Error loading products")
            return
    
    with col2:
        # Forecast parameters
        horizon_days = st.number_input("Forecast Horizon (days)", min_value=1, max_value=365, value=30)
        method = st.selectbox(
            "Forecasting Method",
            ["auto", "moving_average", "exponential_smoothing", "trend_analysis"],
            format_func=lambda x: {
                "auto": "Auto (Best Method)",
                "moving_average": "Moving Average",
                "exponential_smoothing": "Exponential Smoothing",
                "trend_analysis": "Trend Analysis"
            }[x]
        )
    
    if st.button("🚀 Generate Forecast"):
        if not selected_product:
            st.error("Please select a product")
            return
        
        with st.spinner("Generating forecast..."):
            try:
                # Generate forecast
                forecast_result = forecasting_service.generate_forecast(
                    product_id=product.id,
                    horizon=horizon_days,
                    method=method
                )
                
                if "error" in forecast_result:
                    st.error(f"Forecast generation failed: {forecast_result['error']}")
                    return
                
                # Display results
                st.success("✅ Forecast generated successfully!")
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Forecast Method", forecast_result['forecast_method'].replace('_', ' ').title())
                
                with col2:
                    st.metric("Total Forecast", f"{forecast_result['total_forecast']:.1f} units")
                
                with col3:
                    st.metric("Daily Average", f"{forecast_result['daily_average']:.1f} units/day")
                
                with col4:
                    st.metric("Data Points Used", forecast_result['data_points'])
                
                # Forecast visualization
                if forecast_result.get('forecast_series'):
                    st.subheader("📊 Forecast Visualization")
                    
                    # Create forecast chart
                    forecast_dates = [
                        datetime.now() + timedelta(days=i) 
                        for i in range(len(forecast_result['forecast_series']))
                    ]
                    
                    forecast_df = pd.DataFrame({
                        'Date': forecast_dates,
                        'Forecast': forecast_result['forecast_series']
                    })
                    
                    fig = px.line(
                        forecast_df, 
                        x='Date', 
                        y='Forecast',
                        title=f"Demand Forecast for {sku}",
                        labels={'Forecast': 'Predicted Demand (units)'}
                    )
                    
                    # Add historical data if available
                    try:
                        historical_df = forecasting_service.get_historical_demand(product.id, 30)
                        if not historical_df.empty:
                            fig.add_scatter(
                                x=historical_df['date'],
                                y=historical_df['demand'],
                                mode='lines+markers',
                                name='Historical Demand',
                                line=dict(color='gray', dash='dot')
                            )
                    except:
                        pass
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Forecast parameters
                if forecast_result.get('parameters'):
                    st.subheader("🔧 Forecast Parameters")
                    params_df = pd.DataFrame([
                        {"Parameter": k, "Value": v} 
                        for k, v in forecast_result['parameters'].items()
                    ])
                    st.dataframe(params_df, hide_index=True)
                
                # Recommendations
                st.subheader("💡 Recommendations")
                
                current_stock = get_current_stock(inventory_service, sku)
                reorder_point = product.reorder_point if product else 10
                
                if current_stock is not None:
                    days_of_stock = current_stock / forecast_result['daily_average'] if forecast_result['daily_average'] > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"📦 Current Stock: {current_stock} units")
                        st.info(f"⏰ Days of Stock: {days_of_stock:.1f} days")
                    
                    with col2:
                        if days_of_stock < 7:
                            st.error("🚨 Critical: Less than 7 days of stock remaining!")
                        elif days_of_stock < 14:
                            st.warning("⚠️ Warning: Less than 14 days of stock remaining")
                        else:
                            st.success("✅ Stock levels appear adequate")
                
                # Save forecast
                if st.button("💾 Save Forecast"):
                    try:
                        forecasting_service.save_forecast_result(forecast_result)
                        st.success("Forecast saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving forecast: {e}")
                
            except Exception as e:
                st.error(f"Error generating forecast: {e}")

def show_forecast_accuracy(forecasting_service, inventory_service):
    """Show forecast accuracy analysis"""
    st.header("🎯 Forecast Accuracy Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product selection
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Select Product", product_options)
            
            if selected_product:
                sku = selected_product.split(" - ")[0]
                product = inventory_service.get_product_by_sku(sku)
        except:
            st.error("Error loading products")
            return
    
    with col2:
        analysis_days = st.number_input("Analysis Period (days)", min_value=7, max_value=365, value=30)
    
    if st.button("📊 Analyze Accuracy") and selected_product:
        with st.spinner("Analyzing forecast accuracy..."):
            try:
                accuracy_result = forecasting_service.get_forecast_accuracy(product.id, analysis_days)
                
                if "error" in accuracy_result:
                    st.error(f"Accuracy analysis failed: {accuracy_result['error']}")
                    return
                
                st.success("✅ Accuracy analysis completed!")
                
                # Accuracy metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    mae = accuracy_result.get('mean_absolute_error', 0)
                    st.metric("Mean Absolute Error", f"{mae:.2f}")
                
                with col2:
                    mape = accuracy_result.get('mean_absolute_percentage_error', 0)
                    st.metric("Mean Abs. % Error", f"{mape:.1f}%")
                
                with col3:
                    rmse = accuracy_result.get('root_mean_squared_error', 0)
                    st.metric("Root Mean Sq. Error", f"{rmse:.2f}")
                
                with col4:
                    accuracy_score = 100 - min(mape, 100)
                    st.metric("Accuracy Score", f"{accuracy_score:.1f}%")
                
                # Accuracy interpretation
                st.subheader("📈 Accuracy Interpretation")
                
                if mape < 10:
                    st.success("🎯 Excellent accuracy (MAPE < 10%)")
                elif mape < 20:
                    st.info("✅ Good accuracy (MAPE 10-20%)")
                elif mape < 50:
                    st.warning("⚠️ Fair accuracy (MAPE 20-50%)")
                else:
                    st.error("❌ Poor accuracy (MAPE > 50%)")
                
                # Recommendations for improvement
                st.subheader("💡 Improvement Recommendations")
                
                if accuracy_result.get('data_points', 0) < 30:
                    st.info("📊 More historical data needed for better accuracy")
                
                if mape > 20:
                    st.info("🔧 Consider trying different forecasting methods")
                    st.info("📊 Check for seasonal patterns or trends")
                
                # Forecast vs Actual chart (mock data)
                st.subheader("📊 Forecast vs Actual")
                
                # Generate mock comparison data
                dates = [datetime.now() - timedelta(days=i) for i in range(analysis_days, 0, -1)]
                mock_actual = [max(0, 10 + i * 0.5 + (i % 7) * 2) for i in range(analysis_days)]
                mock_forecast = [max(0, actual + (actual * 0.1 * (0.5 - (i % 10) / 10))) 
                               for i, actual in enumerate(mock_actual)]
                
                comparison_df = pd.DataFrame({
                    'Date': dates,
                    'Actual': mock_actual,
                    'Forecast': mock_forecast
                })
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=comparison_df['Date'],
                    y=comparison_df['Actual'],
                    mode='lines+markers',
                    name='Actual Demand',
                    line=dict(color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=comparison_df['Date'],
                    y=comparison_df['Forecast'],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='red', dash='dash')
                ))
                
                fig.update_layout(
                    title=f"Forecast vs Actual Demand - {sku}",
                    xaxis_title="Date",
                    yaxis_title="Demand (units)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error analyzing accuracy: {e}")

def show_bulk_forecasting(forecasting_service, inventory_service):
    """Show bulk forecasting for multiple products"""
    st.header("📦 Bulk Forecasting")
    
    st.info("Generate forecasts for multiple products at once.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All Categories"] + get_categories(inventory_service)
        )
    
    with col2:
        horizon_days = st.number_input("Forecast Horizon (days)", min_value=1, max_value=365, value=7)
    
    with col3:
        method = st.selectbox(
            "Forecasting Method",
            ["auto", "moving_average", "exponential_smoothing"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    # Product selection
    try:
        products = inventory_service.list_products(limit=1000)
        
        if category_filter != "All Categories":
            products = [p for p in products if p.category == category_filter]
        
        if not products:
            st.info("No products found for the selected category.")
            return
        
        st.write(f"**Products to forecast:** {len(products)}")
        
        # Show products list
        with st.expander("View Products"):
            products_df = pd.DataFrame([
                {"SKU": p.sku, "Name": p.name, "Category": p.category}
                for p in products
            ])
            st.dataframe(products_df, hide_index=True)
        
        if st.button("🚀 Generate Bulk Forecasts"):
            if len(products) > 50:
                st.error("Maximum 50 products allowed for bulk forecasting")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            successful_forecasts = []
            failed_forecasts = []
            
            for i, product in enumerate(products):
                try:
                    status_text.text(f"Processing {product.sku}...")
                    
                    # Generate forecast
                    forecast_result = forecasting_service.generate_forecast(
                        product_id=product.id,
                        horizon=horizon_days,
                        method=method
                    )
                    
                    if "error" in forecast_result:
                        failed_forecasts.append({
                            "SKU": product.sku,
                            "Error": forecast_result["error"]
                        })
                    else:
                        successful_forecasts.append({
                            "SKU": product.sku,
                            "Product Name": product.name,
                            "Method": forecast_result["forecast_method"],
                            "Total Forecast": f"{forecast_result['total_forecast']:.1f}",
                            "Daily Average": f"{forecast_result['daily_average']:.1f}",
                            "Data Points": forecast_result["data_points"]
                        })
                        
                        # Save forecast
                        forecasting_service.save_forecast_result(forecast_result)
                    
                    # Update progress
                    progress = (i + 1) / len(products)
                    progress_bar.progress(progress)
                    
                except Exception as e:
                    failed_forecasts.append({
                        "SKU": product.sku,
                        "Error": str(e)
                    })
            
            # Show results
            status_text.text("Bulk forecasting completed!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Successful Forecasts", len(successful_forecasts))
            
            with col2:
                st.metric("Failed Forecasts", len(failed_forecasts))
            
            # Show successful forecasts
            if successful_forecasts:
                st.subheader("✅ Successful Forecasts")
                success_df = pd.DataFrame(successful_forecasts)
                st.dataframe(success_df, hide_index=True)
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                
                total_forecast = sum(float(f["Total Forecast"]) for f in successful_forecasts)
                avg_daily = sum(float(f["Daily Average"]) for f in successful_forecasts)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Forecasted Demand", f"{total_forecast:.1f} units")
                
                with col2:
                    st.metric("Total Daily Average", f"{avg_daily:.1f} units/day")
            
            # Show failed forecasts
            if failed_forecasts:
                st.subheader("❌ Failed Forecasts")
                failed_df = pd.DataFrame(failed_forecasts)
                st.dataframe(failed_df, hide_index=True)
            
            # Export option
            if successful_forecasts:
                if st.button("📥 Export Results"):
                    csv = pd.DataFrame(successful_forecasts).to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"bulk_forecasts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
    except Exception as e:
        st.error(f"Error in bulk forecasting: {e}")

def show_seasonal_analysis(forecasting_service, inventory_service):
    """Show seasonal pattern analysis"""
    st.header("🌊 Seasonal Pattern Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product selection
        try:
            products = inventory_service.list_products(limit=1000)
            product_options = [f"{p.sku} - {p.name}" for p in products]
            selected_product = st.selectbox("Select Product", product_options)
            
            if selected_product:
                sku = selected_product.split(" - ")[0]
                product = inventory_service.get_product_by_sku(sku)
        except:
            st.error("Error loading products")
            return
    
    with col2:
        st.write("")  # Spacer
    
    if st.button("🔍 Analyze Seasonal Patterns") and selected_product:
        with st.spinner("Analyzing seasonal patterns..."):
            try:
                seasonal_result = forecasting_service.get_seasonal_patterns(product.id)
                
                if "error" in seasonal_result:
                    st.error(f"Seasonal analysis failed: {seasonal_result['error']}")
                    return
                
                st.success("✅ Seasonal analysis completed!")
                
                # Seasonal detection
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    seasonal_detected = seasonal_result.get('seasonal_detected', False)
                    st.metric("Seasonality Detected", "Yes" if seasonal_detected else "No")
                
                with col2:
                    cv = seasonal_result.get('coefficient_of_variation', 0)
                    st.metric("Coefficient of Variation", f"{cv:.2f}")
                
                with col3:
                    data_points = seasonal_result.get('data_points', 0)
                    st.metric("Data Points Analyzed", data_points)
                
                # Day of week pattern
                if seasonal_result.get('day_of_week_pattern'):
                    st.subheader("📅 Day of Week Pattern")
                    
                    dow_pattern = seasonal_result['day_of_week_pattern']
                    dow_df = pd.DataFrame([
                        {"Day": day, "Relative Demand": demand}
                        for day, demand in dow_pattern.items()
                    ])
                    
                    # Order days correctly
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    dow_df['Day'] = pd.Categorical(dow_df['Day'], categories=day_order, ordered=True)
                    dow_df = dow_df.sort_values('Day')
                    
                    fig = px.bar(
                        dow_df,
                        x='Day',
                        y='Relative Demand',
                        title="Demand Pattern by Day of Week",
                        labels={'Relative Demand': 'Relative Demand (1.0 = average)'}
                    )
                    
                    # Add average line
                    fig.add_hline(y=1.0, line_dash="dash", line_color="red", 
                                 annotation_text="Average")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interpretation
                    highest_day = dow_df.loc[dow_df['Relative Demand'].idxmax(), 'Day']
                    lowest_day = dow_df.loc[dow_df['Relative Demand'].idxmin(), 'Day']
                    
                    st.info(f"📈 Highest demand: {highest_day}")
                    st.info(f"📉 Lowest demand: {lowest_day}")
                
                # Seasonality insights
                st.subheader("💡 Seasonal Insights")
                
                if seasonal_detected:
                    st.success("🌊 Strong seasonal patterns detected!")
                    st.info("✅ Consider seasonal forecasting methods")
                    st.info("📊 Plan inventory levels based on seasonal demand")
                    
                    if cv > 0.5:
                        st.warning("⚠️ High demand variability - consider safety stock adjustments")
                else:
                    st.info("📊 No strong seasonal patterns detected")
                    st.info("✅ Standard forecasting methods should work well")
                
                if data_points < 90:
                    st.warning("📊 Limited data for seasonal analysis - collect more historical data for better insights")
                
                # Recommendations
                st.subheader("🎯 Recommendations")
                
                recommendations = []
                
                if seasonal_detected:
                    recommendations.append("Use seasonal forecasting methods (e.g., seasonal decomposition)")
                    recommendations.append("Adjust safety stock levels based on seasonal patterns")
                    recommendations.append("Plan promotions and inventory builds around peak seasons")
                
                if cv > 0.3:
                    recommendations.append("Consider dynamic safety stock calculations")
                    recommendations.append("Implement more frequent demand reviews")
                
                if dow_pattern:
                    peak_days = [day for day, demand in dow_pattern.items() if demand > 1.2]
                    if peak_days:
                        recommendations.append(f"Ensure adequate stock for peak days: {', '.join(peak_days)}")
                
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
                
            except Exception as e:
                st.error(f"Error analyzing seasonal patterns: {e}")

def get_current_stock(inventory_service, sku: str):
    """Get current total stock for a product"""
    try:
        stock_levels = inventory_service.get_stock_levels(sku)
        if stock_levels:
            return sum(item['quantity'] for item in stock_levels)
        return 0
    except:
        return None

def get_categories(inventory_service) -> list:
    """Get list of product categories"""
    try:
        products = inventory_service.list_products(limit=1000)
        categories = list(set(p.category for p in products))
        return sorted(categories)
    except:
        return []

if __name__ == "__main__":
    render_forecasting_page()
