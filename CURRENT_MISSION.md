# CURRENT MISSION

## Trenutna misija

Fokus razvoja AI Alpha Enginea uvijek je usmjeren na **jednu aktivnu fazu** definiranu u ROADMAP.md.

Cilj ovog dokumenta je jasno odrediti na čemu trenutno radimo, zašto to radimo i koji su kriteriji završetka prije prelaska na sljedeću fazu.

---

# Trenutna faza

**Phase 2 – Research Engine**

Phase 1 – Data Foundation službeno je završena.

Sustav može pouzdano prikupljati, obrađivati, spremati i vizualizirati tržišne podatke.

Početna implementacija Backtesting Enginea već postoji i koristila se za validaciju cjelokupnog pipelinea. Njegov daljnji razvoj nastavlja se u Phase 2.
---



# Trenutni modul

**Research Engine**

Prvi cilj Phase 2 je izgraditi pouzdan okvir za razvoj, testiranje i objektivnu evaluaciju trading strategija.

Početna EMA Strategy ostaje referentna (baseline) strategija koja će služiti za usporedbu svih budućih strategija.

Prvi modul koji razvijamo u ovoj fazi je:

**Feature Engine**
---

# Zašto je ova faza važna?

Nakon što je Data Foundation uspješno dovršena, AI Alpha Engine sada može prijeći na istraživanje tržišta i razvoj strategija.

Cilj ove faze je objektivno razvijati, testirati i uspoređivati različite trading strategije koristeći pouzdane tržišne podatke.

Research Engine predstavlja početak procesa pronalaženja statistički održivog edgea.
---

# Trenutni zadaci

- definirati arhitekturu Feature Enginea
- implementirati prvu verziju Feature Engine modula
- odrediti skup početnih tržišnih značajki (features)
- pripremiti podatke za razvoj i usporedbu trading strategija
---

# Što trenutno NE radimo

Ne razvijamo nove funkcionalnosti koje nisu dio trenutne faze.

Ne preskačemo faze definirane u ROADMAP.md.

Ne optimiziramo dijelove sustava koji još nisu dovršeni.

Sve nove ideje bilježimo u LOG.md i vraćamo im se kada dođu na red prema ROADMAP-u.

---

# Kriterij završetka trenutne misije

Misija je završena kada:

- Feature Engine pouzdano generira definirane tržišne značajke
- Feature Engine je integriran s postojećim pipelineom
- EMA Strategy može koristiti generirane featurese
- nema poznatih kritičnih grešaka

---



---

# Pravilo fokusa

Prije svake razvojne odluke postavljamo jedno pitanje:

> **"Je li ovo dio naše trenutne misije?"**

Ako je odgovor **DA**, nastavljamo razvoj.

Ako je odgovor **NE**, ideju zapisujemo u LOG.md i nastavljamo s trenutačnom fazom.

Na taj način AI Alpha Engine razvijamo planski, bez gubitka fokusa i bez preskakanja koraka.