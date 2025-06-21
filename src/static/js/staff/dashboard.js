import { capitalize } from "../utils.js";

const date = new Date();

const formattedDate = date.toLocaleDateString("en-US", {
  weekday: "long",
  year: "numeric",
  month: "long",
  day: "numeric",
});

const year = date.getFullYear();
const yearStart = new Date(year, 0, 1);
const weekNumber = Math.ceil(
  ((date - yearStart) / 86400000 + yearStart.getDay() + 1) / 7
);

document.getElementById("dashboard__week").textContent = `Week ${weekNumber}`;
document.getElementById("dashboard__date").textContent =
  capitalize(formattedDate);
