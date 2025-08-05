import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Inventory Accuracy Checker", layout="wide")
st.title("🎯 Inventory Accuracy Checker")

st.markdown("Upload two inventory Excel files generated from the daily inventory app to compare their accuracy.")

# رفع ملفين الجرد
inv_file_1 = st.file_uploader("📁 Upload First Inventory File", type=['xlsx'], key='inv1')
inv_file_2 = st.file_uploader("📁 Upload Second Inventory File", type=['xlsx'], key='inv2')

if inv_file_1 and inv_file_2:
    try:
        # قراءة كل الشيتات
        df1 = pd.read_excel(inv_file_1, sheet_name=None)
        df2 = pd.read_excel(inv_file_2, sheet_name=None)

        # دمج البراندات داخل كل ملف
        def combine_inventory_data(sheet_dict):
            combined_df = pd.DataFrame()
            for sheet_name, sheet in sheet_dict.items():
                if set(['Barcodes', 'Product Name', 'Actual Quantity']).issubset(sheet.columns):
                    sheet = sheet[['Barcodes', 'Product Name', 'Actual Quantity']]
                    sheet = sheet.dropna(subset=['Barcodes'])
                    combined_df = pd.concat([combined_df, sheet], ignore_index=True)
            return combined_df

        inv1_df = combine_inventory_data(df1)
        inv2_df = combine_inventory_data(df2)

        # تجهيز الأعمدة
        inv1_df = inv1_df.rename(columns={'Actual Quantity': 'Qty_1'})
        inv2_df = inv2_df.rename(columns={'Actual Quantity': 'Qty_2'})

        # دمج الاتنين على الباركود
        merged = pd.merge(inv1_df, inv2_df, on='Barcodes', how='outer')
        merged['Product Name'] = merged['Product Name_x'].combine_first(merged['Product Name_y'])
        merged = merged[['Barcodes', 'Product Name', 'Qty_1', 'Qty_2']]

        merged['Qty_1'] = merged['Qty_1'].fillna(0)
        merged['Qty_2'] = merged['Qty_2'].fillna(0)

        # حساب الفرق
        merged['Difference'] = abs(merged['Qty_1'] - merged['Qty_2'])

        # المؤشرات
        total_items = len(merged)
        exact_matches = (merged['Difference'] == 0).sum()
        match_rate = exact_matches / total_items * 100
        average_difference = merged['Difference'].mean()
        total_difference = merged['Difference'].sum()

        accuracy_2 = 100 - (total_difference / merged['Qty_1'].sum() * 100) if merged['Qty_1'].sum() > 0 else 0

        # عرض المؤشرات
        st.subheader("📊 Accuracy Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Match Rate", f"{match_rate:.2f}%")
        col2.metric("📉 Avg. Difference", f"{average_difference:.2f}")
        col3.metric("📊 Total Difference", f"{total_difference:.0f}")
        col4.metric("🎯 Accuracy (File 2 vs File 1)", f"{accuracy_2:.2f}%")

        # جدول التفاصيل
        st.subheader("📋 Detailed Comparison")
        st.dataframe(merged, use_container_width=True)

        # تصدير التقرير
        output = BytesIO()
        merged.to_excel(output, index=False)
        st.download_button(
            "📥 Download Comparison Report",
            data=output.getvalue(),
            file_name="Inventory_Comparison_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error while processing files: {e}")
