function mfGetLocation(onOk) {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    (pos) => onOk(pos.coords.latitude, pos.coords.longitude),
    () => {},
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
  );
}

function mfAttachLocationToForm(form) {
  const latInput = form.querySelector('input[name="lat"]');
  const lngInput = form.querySelector('input[name="lng"]');
  if (!latInput || !lngInput) return;
  mfGetLocation((lat, lng) => {
    latInput.value = String(lat);
    lngInput.value = String(lng);
  });
}

function mfSetupSuggest(inputId, endpointUrl) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const wrap = input.closest(".position-relative") || input.parentElement;
  const box = document.createElement("div");
  box.className = "suggest-box";
  box.innerHTML = `<div class="list-group shadow-sm"></div>`;
  wrap.appendChild(box);
  const list = box.querySelector(".list-group");

  let timer = null;
  async function fetchSuggest(q) {
    const url = `${endpointUrl}?q=${encodeURIComponent(q)}`;
    const res = await fetch(url, { headers: { "X-Requested-With": "fetch" } });
    return await res.json();
  }

  function clear() {
    list.innerHTML = "";
    box.style.display = "none";
  }

  input.addEventListener("input", () => {
    const q = input.value.trim();
    if (timer) clearTimeout(timer);
    if (q.length < 2) return clear();
    timer = setTimeout(async () => {
      try {
        const data = await fetchSuggest(q);
        const items = (data && data.results) || [];
        if (!items.length) return clear();
        list.innerHTML = items
          .map((name) => `<button type="button" class="list-group-item list-group-item-action suggest-item">${name}</button>`)
          .join("");
        box.style.display = "block";
        list.querySelectorAll(".suggest-item").forEach((btn) => {
          btn.addEventListener("click", () => {
            input.value = btn.textContent;
            clear();
            input.focus();
          });
        });
      } catch {
        clear();
      }
    }, 180);
  });

  document.addEventListener("click", (e) => {
    if (!box.contains(e.target) && e.target !== input) clear();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.getElementById("mf-search-form");
  if (searchForm) mfAttachLocationToForm(searchForm);

  const suggestEl = document.getElementById("mf-search-input");
  if (suggestEl) mfSetupSuggest("mf-search-input", "/suggest/");
});

