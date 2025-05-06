fetch('http://127.0.0.1:5000/api/listes')
    .then(response => response.json())
    .then(data => {
        const listesDiv = document.getElementById('listes');
        data.forEach(famille => {
            const liste = document.createElement('div');
            liste.innerHTML = `<h2>${famille.nom}</h2><ul>${famille.cadeaux.map(cadeau => `<li>${cadeau}</li>`).join('')}</ul>`;
            listesDiv.appendChild(liste);
        });
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
