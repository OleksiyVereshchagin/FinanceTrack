// // Функціонал перемикання полів дат
// function initDateFilters() {
//     const periodSelect = document.getElementById('id_period');
//     const customDates = document.getElementById('custom-dates');
//     const customDatesEnd = document.getElementById('custom-dates-end');
//
//     function toggleDateFields() {
//         const isCustom = periodSelect.value === 'custom';
//         customDates.style.display = isCustom ? 'block' : 'none';
//         customDatesEnd.style.display = isCustom ? 'block' : 'none';
//     }
//
//     periodSelect.addEventListener('change', toggleDateFields);
//     toggleDateFields(); // Ініціалізація при завантаженні
// }
//
// // Ініціалізація кругової діаграми
// function initCategoryChart(labels, data) {
//     return new Chart(document.getElementById('categoryChart'), {
//         type: 'doughnut',
//         data: {
//             labels: labels,
//             datasets: [{
//                 data: data,
//                 backgroundColor: ['#C1E6CB', '#A8D8EA', '#F8B195']
//             }]
//         }
//     });
// }
//
// // Ініціалізація лінійного графіка
// function initDailyChart(labels, data) {
//     return new Chart(document.getElementById('dailyChart'), {
//         type: 'line',
//         data: {
//             labels: labels,
//             datasets: [{
//                 label: 'Витрати',
//                 data: data,
//                 borderColor: '#C1E6CB'
//             }]
//         }
//     });
// }
//
// // Основна функція ініціалізації
// document.addEventListener('DOMContentLoaded', function() {
//     initDateFilters();
//
//     // Отримуємо дані з data-атрибутів
//     const categoryChartEl = document.getElementById('categoryChart');
//     const dailyChartEl = document.getElementById('dailyChart');
//
//     if (categoryChartEl) {
//         initCategoryChart(
//             JSON.parse(categoryChartEl.dataset.labels),
//             JSON.parse(categoryChartEl.dataset.values)
//         );
//     }
//
//     if (dailyChartEl) {
//         initDailyChart(
//             JSON.parse(dailyChartEl.dataset.labels),
//             JSON.parse(dailyChartEl.dataset.values)
//         );
//     }
// });