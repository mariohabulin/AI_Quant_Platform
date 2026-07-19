# CURRENT MISSION

## Trenutna misija

Fokus razvoja AI Alpha Enginea uvijek je usmjeren na **jednu aktivnu fazu** definiranu u ROADMAP.md.

Cilj ovog dokumenta je jasno odrediti na čemu trenutno radimo, zašto to radimo i koji su kriteriji završetka prije prelaska na sljedeću fazu.

---

# Trenutna faza

**Phase 1 – Data Foundation**
Napomena:

Data Foundation je funkcionalno dovršena.

Trenutna misija predstavlja završnu validaciju sustava prije prelaska na Phase 2 – Research Engine.

---

# Trenutni modul

**EMA Strategy**

---

Dovršiti razvoj EMA Strategy modula koji generira BUY i SELL signale.

Strategija mora ispravno generirati Signal stupac koji će koristiti Backtest i Data Visualization.

Cilj je dovršiti cijeli razvojni lanac:

Data Loader
→ EMA Strategy
→ Data Visualization

---

# Zašto je ova faza važna?

Kvalitetne odluke ovise o kvalitetnim podacima.

Prije nego AI može pronaći statistički održiv edge, mora imati potpuno pouzdane podatke i mogućnost njihove analize.

Data Foundation predstavlja temelj cijelog AI Alpha Enginea.

---

# Trenutni zadaci

- implementirati BUY signale
- implementirati SELL signale
- generirati Signal stupac
- provjeriti ispravnost EMA strategije
- potvrditi prikaz BUY/SELL markera u Data Visualization

---

# Što trenutno NE radimo

Ne razvijamo nove funkcionalnosti koje nisu dio trenutne faze.

Ne preskačemo faze definirane u ROADMAP.md.

Ne optimiziramo dijelove sustava koji još nisu dovršeni.

Sve nove ideje bilježimo u LOG.md i vraćamo im se kada dođu na red prema ROADMAP-u.

---

# Kriterij završetka

Misija je završena kada:

- EMA Strategy generira ispravne BUY signale
- EMA Strategy generira ispravne SELL signale
- Signal stupac je ispravno spremljen
- Data Visualization prikazuje BUY/SELL markere
- nema poznatih kritičnih grešaka

---

# Sljedeća faza

**Phase 2 – Research Engine**

Prvi korak:

**Feature Engine**

---

# Pravilo fokusa

Prije svake razvojne odluke postavljamo jedno pitanje:

> **"Je li ovo dio naše trenutne misije?"**

Ako je odgovor **DA**, nastavljamo razvoj.

Ako je odgovor **NE**, ideju zapisujemo u LOG.md i nastavljamo s trenutačnom fazom.

Na taj način AI Alpha Engine razvijamo planski, bez gubitka fokusa i bez preskakanja koraka.