# Procédure de déploiement — Labo 09 (Base de données distribuée)

Ce document décrit la mise en production de l'application Store Manager simplifiée avec la base
de données distribuée retenue, **CockroachDB** (voir `docs/adr/adr001.md`), sur une machine
virtuelle (VM), ainsi que l'automatisation du déploiement via un **GitHub self-hosted runner**
et le pipeline CI/CD (`.github/workflows/ci.yml`).

---

## 1. Choix de la base de données

Après les tests de charge du Labo 09 (activités 3 et 5), nous avons retenu **CockroachDB**
comme base de données distribuée de production. Justification :

- **Performances supérieures** dans nos tests : débit ×2.25 (57 vs 25 req/s) et latence ÷3
  (468 vs 1389 ms) par rapport à YugabyteDB, sur des paramètres Locust identiques ;
- Distribution et réplication natives (consensus **MultiRaft**) sans point de défaillance unique ;
- Compatibilité PostgreSQL (le pilote `psycopg2` et SQLAlchemy fonctionnent sans modification) ;
- Isolation **SERIALIZABLE** par défaut, qui gère nativement les conflits transactionnels.

> **Réserve :** CockroachDB est *source available* et n'est pas gratuit pour un usage commercial
> (gratuit pour usage personnel/éducatif). Si une licence 100 % open source devenait une exigence
> ferme, **YugabyteDB** serait l'alternative — la procédure ci-dessous est quasi identique : il
> suffit d'utiliser le répertoire `yugabyte-db/` au lieu de `cockroach-db/`.

---

## 2. Provisionnement de la VM

| Élément | Recommandation minimale |
|---------|--------------------------|
| OS | Ubuntu Server 22.04 LTS |
| vCPU | 4 (2 minimum) |
| RAM | 8 Go (3 nœuds CockroachDB) |
| Disque | 20 Go SSD |
| Réseau | Ports ouverts : `5000` (API), `8085` (Admin UI CockroachDB), `8089` (Locust) |

### Installation de Docker sur la VM

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER   # déconnexion/reconnexion ensuite
```

---

## 3. Déploiement manuel (première fois)

```bash
# 1. Cloner le dépôt
git clone https://github.com/ralphgabriel04/log430-labo9.git
cd log430-labo9/cockroach-db

# 2. Créer le fichier .env
cp .env.example .env

# 3. Démarrer le cluster (3 nœuds + init + app Flask + Locust)
docker compose up -d --build

# 4. Vérifier l'état du cluster
docker compose ps
curl http://localhost:5000/health        # {"status":"ok"}
curl http://localhost:5000/stocks         # liste des stocks
```

Interfaces accessibles :
- **API REST** : `http://<IP_VM>:5000`
- **CockroachDB Admin UI** : `http://<IP_VM>:8085`
- **Locust** : `http://<IP_VM>:8089`

> ⚠️ Notes d'environnement rencontrées au Labo 9 :
> - Les scripts `db-init/entrypoint.sh` doivent avoir des **fins de ligne LF** (un `.gitattributes`
>   force `eol=lf`) sinon ils échouent dans le conteneur Linux (`$'\r': command not found`).
> - L'Admin UI est mappée sur le port hôte **8085** (le 8080 était déjà occupé localement).

---

## 4. Déploiement automatisé (CI/CD + GitHub self-hosted runner)

### 4.1 Installer le runner sur la VM

Dans GitHub : *Settings → Actions → Runners → New self-hosted runner* (Linux x64), puis sur la VM :

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-linux-x64-2.317.0.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/ralphgabriel04/log430-labo9 --token <TOKEN_FOURNI_PAR_GITHUB>
sudo ./svc.sh install     # installe le runner comme service systemd
sudo ./svc.sh start
```

### 4.2 Pipeline CI/CD

Le fichier `.github/workflows/ci.yml` définit deux étapes :

1. **`concurrency-test`** (sur runner GitHub hébergé) :
   - démarre un cluster CockroachDB éphémère ;
   - exécute `concurrency_test.py --threads 20 --product 3` ;
   - **bloque le déploiement** si le verrou distribué échoue (stock article 3 ≠ 0).

2. **`deploy`** (déclenché seulement si les tests passent, sur `main`) :
   - se connecte à la VM (par SSH, ou directement si on cible le self-hosted runner) ;
   - `git pull` puis `docker compose up -d --build`.

### 4.3 Secrets GitHub à configurer

Pour le déploiement par SSH (*Settings → Secrets and variables → Actions*) :

| Secret | Description |
|--------|-------------|
| `VM_HOST` | adresse IP ou DNS de la VM |
| `VM_USER` | utilisateur SSH (ex. `ubuntu`) |
| `VM_SSH_KEY` | clé privée SSH autorisée sur la VM |

> Variante self-hosted runner : remplacer `runs-on: ubuntu-latest` du job `deploy` par
> `runs-on: self-hosted` et exécuter directement les commandes `docker compose` sur la VM,
> sans passer par SSH.

---

## 5. Exploitation

```bash
# Suivre les logs de l'application
docker compose logs -f python-app

# Redémarrer un nœud (test de résilience)
docker stop cockroach2
docker start cockroach2

# Mettre à jour après un nouveau commit
git pull origin main && docker compose up -d --build

# Tout arrêter (en conservant les données)
docker compose down

# Tout arrêter et supprimer les volumes (remise à zéro)
docker compose down -v
```
