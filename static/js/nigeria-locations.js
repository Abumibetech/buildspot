(function () {
    "use strict";

    const locations = {"Abia": ["Umuahia", "Aba", "Ohafia"], "Adamawa": ["Yola", "Mubi", "Jimeta", "Numan"], "Akwa Ibom": ["Uyo", "Eket", "Ikot Ekpene", "Oron"], "Anambra": ["Awka", "Onitsha", "Nnewi", "Ekwulobia"], "Bauchi": ["Bauchi", "Azare", "Misau", "Jama'are"], "Bayelsa": ["Yenagoa", "Brass", "Ogbia", "Nembe"], "Benue": ["Makurdi", "Gboko", "Otukpo", "Katsina-Ala"], "Borno": ["Maiduguri", "Biu", "Bama", "Monguno"], "Cross River": ["Calabar", "Ikom", "Ogoja", "Obudu"], "Delta": ["Asaba", "Warri", "Effurun", "Sapele", "Ughelli", "Agbor"], "Ebonyi": ["Abakaliki", "Afikpo", "Onueke"], "Edo": ["Benin City", "Auchi", "Ekpoma", "Uromi"], "Ekiti": ["Ado-Ekiti", "Ikere-Ekiti", "Ijero-Ekiti", "Ilawe-Ekiti"], "Enugu": ["Enugu", "Nsukka", "Agbani", "Udi", "Oji River"], "Federal Capital Territory (FCT)": ["Abuja", "Gwagwalada", "Kubwa", "Bwari", "Kuje", "Lugbe", "Garki", "Wuse", "Maitama", "Asokoro"], "Gombe": ["Gombe", "Kumo", "Billiri", "Dukku"], "Imo": ["Owerri", "Orlu", "Okigwe", "Mbaise"], "Jigawa": ["Dutse", "Hadejia", "Kazaure", "Gumel"], "Kaduna": ["Kaduna", "Zaria", "Kafanchan", "Saminaka"], "Kano": ["Kano", "Wudil", "Gwarzo", "Rano"], "Katsina": ["Katsina", "Daura", "Funtua", "Malumfashi"], "Kebbi": ["Birnin Kebbi", "Argungu", "Yauri", "Zuru"], "Kogi": ["Lokoja", "Okene", "Idah", "Kabba"], "Kwara": ["Ilorin", "Offa", "Jebba", "Lafiagi"], "Lagos": ["Ikeja", "Lagos Island", "Victoria Island", "Lekki", "Ikorodu", "Epe", "Badagry", "Surulere", "Yaba", "Ajah", "Festac"], "Nasarawa": ["Lafia", "Keffi", "Akwanga", "Karu", "Mararaba"], "Niger": ["Minna", "Bida", "Suleja", "Kontagora", "New Bussa"], "Ogun": ["Abeokuta", "Ijebu-Ode", "Sagamu", "Ota", "Ilaro"], "Ondo": ["Akure", "Ondo", "Owo", "Ikare-Akoko"], "Osun": ["Osogbo", "Ile-Ife", "Ilesa", "Ede", "Ikirun"], "Oyo": ["Ibadan", "Ogbomoso", "Oyo", "Iseyin", "Saki"], "Plateau": ["Jos", "Bukuru", "Pankshin", "Shendam"], "Rivers": ["Port Harcourt", "Bonny", "Omoku", "Eleme", "Ahoada"], "Sokoto": ["Sokoto", "Tambuwal", "Wurno", "Gwadabawa"], "Taraba": ["Jalingo", "Wukari", "Bali", "Serti"], "Yobe": ["Damaturu", "Potiskum", "Gashua", "Nguru"], "Zamfara": ["Gusau", "Kaura Namoda", "Talata Mafara", "Anka"]};
    const stateSelect = document.querySelector('select[name="state"]');
    const citySelect = document.querySelector('select[name="city"]');

    if (!stateSelect || !citySelect) return;

    function populateCities(preserveCurrent) {
        const state = stateSelect.value;
        const previous = preserveCurrent ? citySelect.value : "";
        const cities = locations[state] || [];
        const options = ['<option value="">Select a city or town</option>'];

        cities.forEach(function (city) {
            const option = document.createElement("option");
            option.value = city;
            option.textContent = city;
            options.push(option);
        });

        citySelect.replaceChildren();
        options.forEach(function (item) {
            if (typeof item === "string") {
                const holder = document.createElement("template");
                holder.innerHTML = item;
                citySelect.appendChild(holder.content.firstChild);
            } else {
                citySelect.appendChild(item);
            }
        });

        // Keep an existing saved city visible even if it is not in the starter list.
        if (previous && !cities.includes(previous)) {
            const oldOption = document.createElement("option");
            oldOption.value = previous;
            oldOption.textContent = previous + " (existing location)";
            citySelect.appendChild(oldOption);
        }

        if (previous && Array.from(citySelect.options).some(function (o) {
            return o.value === previous;
        })) {
            citySelect.value = previous;
        }
    }

    stateSelect.addEventListener("change", function () {
        populateCities(false);
    });

    // Preserve the current selection when the page initially loads.
    populateCities(true);
})();