import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Inventory Accuracy Checker", layout="wide")
st.title("🎯 Inventory Accuracy Checker")

st.markdown("Upload two inventory Excel files (from separate counting rounds) to compare their accuracy.")

# رفع ملفين الجرد
inv_file_1 = st.file_uploader("📁 Upload First Inventory File", type=['xlsx'], key='inv1')
inv_file_2 = st.file_uploader("📁 Upload Second Inventory File", type=['xlsx'], key='inv2')

if inv_file_1 and inv_file_2:
    try:
        df1 = pd.read_excel(inv_file_1, sheet_name=None)
        df2 = pd.read_excel(inv_file_2, sheet_name=None)

        def combine_inventory_data(sheet_dict):
            combined_df = pd.DataFrame()
            for sheet_name, sheet in sheet_dict.items():
                if set(['Barcodes', 'Product Name', 'Actual Quantity']).issubset(sheet.columns):
                    sheet = sheet[['Barcodes', 'Product Name', 'Actual Quantity']].copy()
                    sheet['Brand'] = sheet_name  # نستخدم اسم الشيت كبراند
                    sheet = sheet.dropna(subset=['Barcodes'])
                    combined_df = pd.concat([combined_df, sheet], ignore_index=True)
            return combined_df

        inv1_df = combine_inventory_data(df1).rename(columns={'Actual Quantity': 'Qty_1'})
        inv2_df = combine_inventory_data(df2).rename(columns={'Actual Quantity': 'Qty_2'})

        merged = pd.merge(inv1_df, inv2_df, on='Barcodes', how='outer')
        merged['Product Name'] = merged['Product Name_x'].combine_first(merged['Product Name_y'])
        merged['Brand'] = merged['Brand_x'].combine_first(merged['Brand_y'])

        merged = merged[['Barcodes', 'Product Name', 'Brand', 'Qty_1', 'Qty_2']]
        merged['Qty_1'] = merged['Qty_1'].fillna(0)
        merged['Qty_2'] = merged['Qty_2'].fillna(0)
        merged['Difference'] = abs(merged['Qty_1'] - merged['Qty_2'])

        # الحساب العام
        total_difference = merged['Difference'].sum()
        base_total = merged[['Qty_1', 'Qty_2']].sum(axis=1).sum() / 2
        accuracy = 100 - (total_difference / base_total * 100) if base_total > 0 else 0
        match_rate = (merged['Difference'] == 0).sum() / len(merged) * 100
        avg_diff = merged['Difference'].mean()

        st.subheader("📊 Overall Accuracy Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Match Rate", f"{match_rate:.2f}%")
        col2.metric("📉 Avg. Difference", f"{avg_diff:.2f}")
        col3.metric("📊 Total Difference", f"{total_difference}")
        col4.metric("🎯 Accuracy", f"{accuracy:.2f}%")

        # الحساب لكل براند
        st.subheader("🏷️ Accuracy per Brand")
        brand_summary = merged.groupby('Brand').agg({
            'Qty_1': 'sum',
            'Qty_2': 'sum',
            'Difference': 'sum'
        }).reset_index()

        brand_summary['Base Total'] = (brand_summary['Qty_1'] + brand_summary['Qty_2']) / 2
        brand_summary['Accuracy %'] = 100 - (brand_summary['Difference'] / brand_summary['Base Total'] * 100)
        brand_summary['Accuracy %'] = brand_summary['Accuracy %'].fillna(0)

        brand_summary_display = brand_summary[['Brand', 'Qty_1', 'Qty_2', 'Difference', 'Accuracy %']]
        st.dataframe(brand_summary_display)

        # جدول التفاصيل
        with st.expander("📋 Show Detailed Comparison Table"):
            st.dataframe(merged)

        # تصدير التقرير
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            merged.to_excel(writer, sheet_name='Detailed Comparison', index=False)
            brand_summary_display.to_excel(writer, sheet_name='Brand Accuracy Summary', index=False)

        st.download_button(
            "📥 Download Full Accuracy Report",
            data=output.getvalue(),
            file_name="Inventory_Accuracy_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error while processing files: {e}")
