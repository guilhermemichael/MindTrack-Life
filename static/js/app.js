document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = nextTheme;
  localStorage.setItem("mindtrack-theme", nextTheme);
});

document.querySelector("[data-menu-toggle]")?.addEventListener("click", () => {
  document.body.classList.toggle("nav-open");
});

document.querySelectorAll("[data-range-input]").forEach((input) => {
  const output = input.parentElement?.querySelector("output");
  const sync = () => {
    if (output) {
      output.textContent = input.value;
    }
  };

  sync();
  input.addEventListener("input", sync);
});
