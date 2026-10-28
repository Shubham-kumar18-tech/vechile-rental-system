
const search = document.getElementById("search");
const typeFilter = document.getElementById("vehicleType");
const cards = document.querySelectorAll(".card");
const noResults = document.getElementById("noResults");

const form = document.getElementById("bookingForm");
const customerName = document.getElementById("customerName");
const vehicleName = document.getElementById("vehicleName");
const vehicleId = document.getElementById("vehicleId");
const pickupDate = document.getElementById("pickupDate");
const returnDate = document.getElementById("returnDate");
const priceSummary = document.getElementById("priceSummary");

let selectedPrice = 0;

function filterVehicles() {
    const query = search.value.trim().toLowerCase();
    const type = typeFilter.value;
    let visible = 0;

    cards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        const category = card.dataset.type;

        const matchesName = name.includes(query);
        const matchesType = type === "all" || category === type;
        const show = matchesName && matchesType;

        card.hidden = !show;
        if (show) visible++;
    });

    noResults.hidden = visible !== 0;
}

search.addEventListener("input", filterVehicles);
typeFilter.addEventListener("change", filterVehicles);

document.querySelectorAll(".book-btn").forEach(button => {
    button.addEventListener("click", () => {
        vehicleId.value = button.dataset.id;
        vehicleName.value = button.dataset.name;
        selectedPrice = Number(button.dataset.price);

        priceSummary.textContent =
            "Select pickup and return dates to estimate the rent.";

        updatePrice();
        document.getElementById("booking").scrollIntoView({
            behavior: "smooth"
        });
    });
});

pickupDate.addEventListener("change", () => {
    returnDate.min = pickupDate.value;

    if (returnDate.value && returnDate.value < pickupDate.value) {
        returnDate.value = "";
    }

    updatePrice();
});

returnDate.addEventListener("change", updatePrice);

function updatePrice() {
    if (!vehicleId.value || !pickupDate.value || !returnDate.value) {
        priceSummary.textContent =
            "Select a vehicle and dates to see the estimate.";
        return;
    }

    if (returnDate.value < pickupDate.value) {
        priceSummary.textContent =
            "Return date must be on or after pickup date.";
        return;
    }

    const start = new Date(pickupDate.value + "T00:00:00");
    const end = new Date(returnDate.value + "T00:00:00");

    const difference = Math.round(
        (end - start) / (1000 * 60 * 60 * 24)
    );

    const days = Math.max(1, difference);
    const total = days * selectedPrice;

    priceSummary.textContent =
        `${days} day(s) × ₹${selectedPrice.toLocaleString("en-IN")} = ₹${total.toLocaleString("en-IN")}`;
}

form.addEventListener("submit", event => {
    if (!vehicleId.value || !selectedPrice) {
        event.preventDefault();
        alert("Please click Book Now on a vehicle first.");
        return;
    }

    if (returnDate.value < pickupDate.value) {
        event.preventDefault();
        alert("Return date must be on or after pickup date.");
    }

    // Valid bookings are submitted to Flask for server-side checks.
});
