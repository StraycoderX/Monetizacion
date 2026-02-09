const form = document.querySelector("#converter-form");
const resultValue = document.querySelector("#result-value");
const resultMeta = document.querySelector("#result-meta");
const resultInfo = document.querySelector("#result-info");
const swapButton = document.querySelector(".swap");

const formatNumber = (value) => {
  const number = Number(value);
  if (Number.isNaN(number)) {
    return "--";
  }
  return new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 4,
  }).format(number);
};

swapButton.addEventListener("click", () => {
  const from = document.querySelector("#from-currency");
  const to = document.querySelector("#to-currency");
  const temp = from.value;
  from.value = to.value;
  to.value = temp;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultInfo.textContent = "";
  resultValue.textContent = "...";

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  payload.amount = payload.amount.trim();

  try {
    const response = await fetch("/convert", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "No se pudo convertir la moneda.");
    }

    resultValue.textContent = `${formatNumber(data.converted_amount)} ${
      data.to_currency
    }`;
    resultMeta.textContent = `${payload.amount} ${data.from_currency} → ${data.to_currency}`;
    resultInfo.textContent = data.exchange_rate
      ? `Tasa utilizada: 1 ${data.from_currency} = ${formatNumber(
          data.exchange_rate
        )} ${data.to_currency}`
      : "";
  } catch (error) {
    resultValue.textContent = "--";
    resultMeta.textContent = "No se pudo completar la conversión.";
    resultInfo.textContent = error.message;
  }
});
