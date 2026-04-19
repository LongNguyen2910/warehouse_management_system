// Chart 1: Inventory by Product (Bar Chart)
async function loadInventoryByProductChart() {
  try {
    const API_URL = "http://localhost:5000/api/reports";
    const response = await fetch(`${API_URL}`, { credentials: "include" });
    const result = await response.json();

    if (!response.ok || !result.success) {
      if (response.status == 401) {
        logout();
        return;
      }
      document.querySelector("#inventoryByProductChart").innerHTML = `
          <div class="alert alert-danger">
            ${result.message}
          </div>
        `;
      return;
    }

    if (result.success && result.data) {
      const productMap = {};
      result.data.forEach((item) => {
        if (!productMap[item.product_name]) {
          productMap[item.product_name] = 0;
        }
        productMap[item.product_name] += item.quantity;
      });

      const categories = Object.keys(productMap).slice(0, 5);
      const data = Object.values(productMap).slice(0, 5);

      const options = {
        chart: { type: "bar", height: 350 },
        plotOptions: { bar: { horizontal: false, columnWidth: "55%" } },
        series: [{ name: "Tồn kho", data: data }],
        xaxis: { categories: categories },
        yaxis: { title: { text: "Số lượng" } },
        colors: ["#696cff"],
        dataLabels: { enabled: false },
      };

      new ApexCharts(
        document.querySelector("#inventoryByProductChart"),
        options,
      ).render();
    }
  } catch (error) {
    console.error("Error loading inventory chart:", error);
    document.querySelector("#inventoryByProductChart").innerHTML =
      '<p class="text-danger">Lỗi tải dữ liệu</p>';
  }
}

// Chart 2: Low Stock Products (Bar Chart)
async function loadLowStockChart() {
  const API_URL = "http://localhost:5000/api/reports/low-stock";
  const response = await fetch(`${API_URL}`, { credentials: "include" });
  const result = await response.json();

  if (!response.ok || !result.success) {
    if (response.status === 401) {
      logout();
      return;
    }
    document.querySelector("#lowStockChart").innerHTML = `
        <div class="alert alert-danger">
          ${result.message}
        </div>
      `;
    return;
  }

  if (result.success && result.data) {
    const data = result.data;
    const categories = data.map((item) => item.product_name).slice(0, 5);
    const needToImport = data.map((item) => item.need_to_import).slice(0, 5);
    const currentStock = data.map((item) => item.total_quantity).slice(0, 5);

    const options = {
      chart: { type: "bar", height: 350 },
      plotOptions: { bar: { horizontal: false, columnWidth: "55%" } },
      series: [
        { name: "Cần nhập thêm", data: needToImport },
        { name: "Tồn kho hiện tại", data: currentStock },
      ],
      xaxis: { categories: categories },
      yaxis: { title: { text: "Số lượng" } },
      colors: ["#ff6b6b", "#51cf66"],
      dataLabels: { enabled: false },
    };

    new ApexCharts(document.querySelector("#lowStockChart"), options).render();
  }
}
// Chart 3: Income
async function loadIncomeChart() {
  const API_URL = "http://localhost:5000/api/receipts/outbound";
  const response = await fetch(`${API_URL}`, { credentials: "include" });

  const data = await response.json();
  // if (!response.ok || !data.success) {
  //   if (response.status === 401) {
  //     logout();
  //     return;
  //   }
  //   document.querySelector("#incomeChart").innerHTML = `
  //       <div class="alert alert-danger">
  //         ${data.message}
  //       </div>
  //     `;
  //   return;
  // }

  // xử lý dữ liệu theo tháng
  const monthly = Array(12).fill(0);

  if (Array.isArray(data)) {
    data.forEach((r) => {
      const month = new Date(r.created_at).getMonth();
      if (Array.isArray(r.items)) {
        r.items.forEach((item) => {
          monthly[month] += item.qty * item.price;
        });
      }
    });
  }

  const chartData = monthly.slice(0, 7);

  // tính total
  const total = monthly.reduce((a, b) => a + b, 0);
  const totalEl = document.querySelector("#totalBalance");
  if (totalEl) {
    totalEl.innerText = total.toLocaleString("vi-VN") + " đ";
  }

  const formatVND = (val) =>
    new Intl.NumberFormat("vi-VN").format(Math.round(val || 0)) + " đ";

  const options = {
    series: [
      {
        name: "Income",
        data: chartData,
      },
    ],
    chart: {
      height: 250,
      type: "area",
      toolbar: { show: false },
      parentHeightOffset: 0,
    },
    stroke: {
      curve: "smooth",
      width: 3,
    },
    colors: ["#696cff"],
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 0.5,
        opacityFrom: 0.4,
        opacityTo: 0.1,
        stops: [0, 90, 100],
      },
    },
    dataLabels: { enabled: false },
    markers: {
      size: 5,
      colors: ["#fff"],
      strokeColors: "#696cff",
      strokeWidth: 3,
      discrete: [
        {
          seriesIndex: 0,
          dataPointIndex: 6,
          fillColor: "#fff",
          strokeColor: "#696cff",
          size: 6,
        },
      ],
    },
    grid: {
      borderColor: "#eee",
      strokeDashArray: 4,
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
    },
    yaxis: {
      labels: {
        formatter: formatVND,
      },
    },
    tooltip: {
      y: {
        formatter: function (val, { series, seriesIndex, dataPointIndex, w }) {
          return val.toLocaleString("vi-VN") + " đ";
        },
        title: {
          formatter: function (seriesName) {
            return "Income";
          },
        },
      },
    },
  };

  new ApexCharts(document.querySelector("#incomeChart"), options).render();
}

// Chart 3: Expenses (Line/Area Chart)
async function loadExpensesChart() {
  try {
    const API_URL = "http://localhost:5000/api/receipts/inbound";
    console.log("Fetching expenses from:", API_URL);
    const response = await fetch(API_URL, { credentials: "include" });

    if (!response.ok) {
      console.error("API error:", response.status, response.statusText);
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log("Expenses data received:", data);

    // xử lý dữ liệu theo tháng
    const monthly = Array(12).fill(0);

    if (Array.isArray(data)) {
      data.forEach((r) => {
        const month = new Date(r.created_at).getMonth();
        if (Array.isArray(r.items)) {
          r.items.forEach((item) => {
            monthly[month] += item.qty * item.price;
          });
        }
      });
    }

    console.log("Monthly data:", monthly);

    const chartData = monthly.slice(0, 7);

    // tính total
    const total = monthly.reduce((a, b) => a + b, 0);
    const totalEl = document.querySelector("#totalBalance");
    if (totalEl) {
      totalEl.innerText = total.toLocaleString("vi-VN") + " đ";
    }

    const formatVND = (val) =>
      new Intl.NumberFormat("vi-VN").format(Math.round(val || 0)) + " đ";

    const options = {
      series: [
        {
          name: "Expenses",
          data: chartData,
        },
      ],
      chart: {
        height: 250,
        type: "area",
        toolbar: { show: false },
        parentHeightOffset: 0,
      },
      stroke: {
        curve: "smooth",
        width: 3,
      },
      colors: ["#ff6b6b"],
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 0.5,
          opacityFrom: 0.4,
          opacityTo: 0.1,
          stops: [0, 90, 100],
        },
      },
      dataLabels: { enabled: false },
      markers: {
        size: 5,
        colors: ["#fff"],
        strokeColors: "#ff6b6b",
        strokeWidth: 3,
        discrete: [
          {
            seriesIndex: 0,
            dataPointIndex: 6,
            fillColor: "#fff",
            strokeColor: "#ff6b6b",
            size: 6,
          },
        ],
      },
      grid: {
        borderColor: "#eee",
        strokeDashArray: 4,
      },
      xaxis: {
        categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
      },
      yaxis: {
        labels: {
          formatter: formatVND,
        },
      },
      tooltip: {
        y: {
          formatter: function (
            val,
            { series, seriesIndex, dataPointIndex, w },
          ) {
            return val.toLocaleString("vi-VN") + " đ";
          },
          title: {
            formatter: function (seriesName) {
              return "Expenses";
            },
          },
        },
      },
    };

    new ApexCharts(document.querySelector("#incomeChart"), options).render();
  } catch (error) {
    console.error("Error loading expenses chart:", error);
    document.querySelector("#incomeChart").innerHTML =
      '<p class="text-danger">Lỗi tải dữ liệu</p>';
  }
}

// Chart 3: Profit (Line/Area Chart)
async function loadProfitChart() {
  try {
    const API_URL_INCOME = "http://localhost:5000/api/receipts/outbound";
    const API_URL_EXPENSES = "http://localhost:5000/api/receipts/inbound";

    const [incomeRes, expensesRes] = await Promise.all([
      fetch(API_URL_INCOME, { credentials: "include" }),
      fetch(API_URL_EXPENSES, { credentials: "include" }),
    ]);

    if (!incomeRes.ok || !expensesRes.ok) {
      throw new Error("API error");
    }

    const incomeData = await incomeRes.json();
    const expensesData = await expensesRes.json();

    // xử lý dữ liệu theo tháng
    const incomeMonthly = Array(12).fill(0);
    const expensesMonthly = Array(12).fill(0);

    if (Array.isArray(incomeData)) {
      incomeData.forEach((r) => {
        const month = new Date(r.created_at).getMonth();
        if (Array.isArray(r.items)) {
          r.items.forEach((item) => {
            incomeMonthly[month] += item.qty * item.price;
          });
        }
      });
    }

    if (Array.isArray(expensesData)) {
      expensesData.forEach((r) => {
        const month = new Date(r.created_at).getMonth();
        if (Array.isArray(r.items)) {
          r.items.forEach((item) => {
            expensesMonthly[month] += item.qty * item.price;
          });
        }
      });
    }

    //profit = income - expenses
    const profitMonthly = incomeMonthly.map(
      (val, idx) => val - expensesMonthly[idx],
    );
    const chartData = profitMonthly.slice(0, 7);

    //total profit
    const total = profitMonthly.reduce((a, b) => a + b, 0);
    const totalEl = document.querySelector("#totalBalance");
    if (totalEl) {
      totalEl.innerText = total.toLocaleString("vi-VN") + " đ";
    }

    const formatVND = (val) =>
      new Intl.NumberFormat("vi-VN").format(Math.round(val || 0)) + " đ";

    const options = {
      series: [
        {
          name: "Profit",
          data: chartData,
        },
      ],
      chart: {
        height: 250,
        type: "area",
        toolbar: { show: false },
        parentHeightOffset: 0,
      },
      stroke: {
        curve: "smooth",
        width: 3,
      },
      colors: ["#51cf66"],
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 0.5,
          opacityFrom: 0.4,
          opacityTo: 0.1,
          stops: [0, 90, 100],
        },
      },
      dataLabels: { enabled: false },
      markers: {
        size: 5,
        colors: ["#fff"],
        strokeColors: "#51cf66",
        strokeWidth: 3,
        discrete: [
          {
            seriesIndex: 0,
            dataPointIndex: 6,
            fillColor: "#fff",
            strokeColor: "#51cf66",
            size: 6,
          },
        ],
      },
      grid: {
        borderColor: "#eee",
        strokeDashArray: 4,
      },
      xaxis: {
        categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
      },
      yaxis: {
        labels: {
          formatter: formatVND,
        },
      },
      tooltip: {
        y: {
          formatter: function (
            val,
            { series, seriesIndex, dataPointIndex, w },
          ) {
            return val.toLocaleString("vi-VN") + " đ";
          },
          title: {
            formatter: function (seriesName) {
              return "Profit";
            },
          },
        },
      },
    };

    new ApexCharts(document.querySelector("#incomeChart"), options).render();
  } catch (error) {
    console.error("Error loading profit chart:", error);
    document.querySelector("#incomeChart").innerHTML =
      '<p class="text-danger">Lỗi tải dữ liệu</p>';
  }
}

function setupChartTabs() {
  const incomeBtn = document.getElementById("incomeBtn");
  const expensesBtn = document.getElementById("expensesBtn");
  const profitBtn = document.getElementById("profitBtn");

  if (incomeBtn) {
    incomeBtn.addEventListener("click", function () {
      updateChartButtons("income");
      document.querySelector("#incomeChart").innerHTML = "";
      loadIncomeChart();
    });
  }

  if (expensesBtn) {
    expensesBtn.addEventListener("click", function () {
      updateChartButtons("expenses");
      document.querySelector("#incomeChart").innerHTML = "";
      loadExpensesChart();
    });
  }

  if (profitBtn) {
    profitBtn.addEventListener("click", function () {
      updateChartButtons("profit");
      document.querySelector("#incomeChart").innerHTML = "";
      loadProfitChart();
    });
  }
}

function updateChartButtons(activeType) {
  const buttons = document.querySelectorAll("[data-chart-type]");
  buttons.forEach((btn) => {
    btn.classList.remove("active");
  });
  document
    .querySelector(`[data-chart-type="${activeType}"]`)
    .classList.add("active");
}

// Initialize all charts
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(() => {
    loadInventoryByProductChart();
    loadLowStockChart();
    loadIncomeChart();
    setupChartTabs();
  }, 100);
});
