// Ajout du style pour le spinner
const style = document.createElement('style');
style.innerHTML = `
.loader-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100px;
}
.spinner {
  border: 6px solid #eee;
  border-top: 6px solid #b44e8a;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
`;
document.head.appendChild(style);

async function chargerListes() {
  const listesDiv = document.getElementById('listes');
  // Création et affichage du spinner
  const spinner = document.createElement('div');
  spinner.className = 'loader-spinner';
  spinner.innerHTML = `<div class="spinner"></div>`;
  listesDiv.innerHTML = '';
  listesDiv.appendChild(spinner);

  try {
    const res = await fetch('https://plaisiroffrir.onrender.com/api/listes');
    const data = await res.json();

    // sort par lists.owner
    data.lists.sort((a, b) => a.owner.localeCompare(b.owner));

    listesDiv.innerHTML = '';

    // Création des onglets
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'tabs-container';
    const tabs = document.createElement('div');
    tabs.className = 'tabs';
    const contents = document.createElement('div');
    contents.className = 'tab-contents';

    data.lists.forEach((liste, idx) => {
      // Onglet
      const tab = document.createElement('button');
      tab.className = 'tab-btn';
      tab.textContent = liste.owner;
      tab.onclick = () => selectTab(idx);
      tabs.appendChild(tab);

      // Contenu de l'onglet
      const content = document.createElement('div');
      content.className = 'tab-content';
      if (idx !== 0) content.style.display = 'none';
      content.innerHTML = `
        <div class="infos">
          <div class="owner">Par <b>${liste.owner}</b></div>
          <h2><a href="${liste.url}" target="_blank" style="color:#b44e8a;text-decoration:none;">
            ${liste.title}
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" style="vertical-align:middle;margin-left:6px;fill:#b44e8a;"><path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3z"/><path d="M5 5h7V3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7H5V5z"/></svg>
          </a></h2>
          <div class="welcome">${liste.welcome_message || ''}</div>
          <div class="presents">
            ${liste.presents
          .slice()
          .sort((a, b) => (b.preference || 0) - (a.preference || 0))
          .map(p => `
                <div class="present">
                  <img class="present-img" src="${p.image_url || ''}" alt="image" onerror="this.style.display='none'">
                  <div class="present-title">${p.title}</div>
                  <div class="present-desc">${p.description || ''}</div>
                  <div class="present-price">
                    ${(p.price === "Pas de prix" || p.price === "Sans limite") ? "Pas de prix" : p.price + "€"}
                  </div>
                  <div class="present-preference">Préférence : ${p.preference || ''}</div>
                  <div class="suggestion">${p.link_suggestion && p.link_suggestion !== 'Pas de lien de suggestion' ? `<a class="present-link" href="${p.link_suggestion}" target="_blank">Suggestion</a>` : ''}</div>
                  <a class="details-link" href="${p.details_link || ''}" target="_blank">Détails / Réserver</a>
                </div>
              `).join('')}
          </div>
        </div>
      `;
      contents.appendChild(content);
    });

    tabsContainer.appendChild(tabs);
    tabsContainer.appendChild(contents);
    listesDiv.appendChild(tabsContainer);

    // Sélection d'un onglet
    function selectTab(idx) {
      const allTabs = tabs.querySelectorAll('.tab-btn');
      const allContents = contents.querySelectorAll('.tab-content');
      allTabs.forEach((t, i) => {
        t.classList.toggle('active', i === idx);
        allContents[i].style.display = i === idx ? '' : 'none';
      });
    }
    // Activer le premier onglet par défaut
    tabs.querySelector('.tab-btn').classList.add('active');
  } catch (e) {
    listesDiv.innerHTML = '<div style="color:red">Erreur de chargement des listes.</div>';
  }
}
chargerListes();
