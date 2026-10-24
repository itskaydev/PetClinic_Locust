import os
import random
import string

import gevent
from locust import HttpUser, between, events, task

WARMUP_SECONDS = int(os.getenv("WARMUP_SECONDS", "60"))
MAX_OWNER_ID = int(os.getenv("MAX_OWNER_ID", "10"))
REQUEST_TIMEOUT = 30

OWNERS = "/api/customer/owners"
VETS = "/api/vet/vets"

CITIES = ["Picos", "Teresina", "Parnaiba", "Floriano", "Oeiras", "Campo Maior"]


def _name(n=7):
    return "".join(random.choices(string.ascii_lowercase, k=n)).capitalize()


def new_owner_payload():
    return {
        "firstName": _name(),
        "lastName": _name(),
        "address": f"Rua {_name(5)}, {random.randint(1, 999)}",
        "city": random.choice(CITIES),
        "telephone": random.choice(string.digits[1:]) + "".join(random.choices(string.digits, k=9)),
    }


@events.test_start.add_listener
def _schedule_warmup_reset(environment, **kwargs):
    if WARMUP_SECONDS <= 0:
        return

    def _reset():
        gevent.sleep(WARMUP_SECONDS)
        environment.stats.reset_all()
        print(f"[locustfile] Aquecimento de {WARMUP_SECONDS}s concluído: estatísticas zeradas.")

    gevent.spawn(_reset)


class _PetClinicUser(HttpUser):
    abstract = True
    wait_time = between(1, 2)

    def op_get_owners(self):
        self.client.get(OWNERS, name="GET /owners", timeout=REQUEST_TIMEOUT)

    def op_get_owner(self):
        owner_id = random.randint(1, MAX_OWNER_ID)
        self.client.get(f"{OWNERS}/{owner_id}", name="GET /owners/{id}", timeout=REQUEST_TIMEOUT)

    def op_get_vets(self):
        self.client.get(VETS, name="GET /vets", timeout=REQUEST_TIMEOUT)

    def op_post_owner(self):
        self.client.post(OWNERS, json=new_owner_payload(), name="POST /owners", timeout=REQUEST_TIMEOUT)


class ReadProfile(_PetClinicUser):
    """Perfil 1 - Leitura (45% / 35% / 15% / 5%)."""

    @task(45)
    def get_owners(self):
        self.op_get_owners()

    @task(35)
    def get_owner(self):
        self.op_get_owner()

    @task(15)
    def get_vets(self):
        self.op_get_vets()

    @task(5)
    def post_owner(self):
        self.op_post_owner()


class WriteProfile(_PetClinicUser):
    """Perfil 2 - Escrita (20% / 20% / 20% / 40%)."""

    @task(20)
    def get_owners(self):
        self.op_get_owners()

    @task(20)
    def get_owner(self):
        self.op_get_owner()

    @task(20)
    def get_vets(self):
        self.op_get_vets()

    @task(40)
    def post_owner(self):
        self.op_post_owner()
