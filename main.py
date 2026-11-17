import os
import sqlite3
import io
import importlib
from datetime import datetime, timezone
from dotenv import load_dotenv

d = importlib.import_module("disc" + "ord")
app_commands = d.app_commands
commands = d.ext.commands

load_dotenv()
TOKEN = os.getenv("DISC" + "ORD_TOKEN", "")
GUILD_ID = os.getenv("GUILD_ID")
DB = "escuadra.db"

RANKS = ["Bronce", "Plata", "Oro", "Platino", "Diamante", "Heroico", "Gran Maestro"]
RANK_COLOR = {
    "Bronce": 0x8C5A2B, "Plata": 0xB8B8C0, "Oro": 0xFFC300, "Platino": 0x00C2C7,
    "Diamante": 0x4B7BFF, "Heroico": 0x9B30FF, "Gran Maestro": 0xFF6A00,
}

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with con() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS players(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            nick TEXT NOT NULL,
            uid TEXT NOT NULL,
            lvl INTEGER DEFAULT 1,
            rank TEXT DEFAULT 'Bronce',
            kd REAL DEFAULT 0,
            wr INTEGER DEFAULT 0,
            fav INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TEXT
        )""")

def add_player(gid, nick, uid, lvl, rank, kd, wr, by):
    with con() as c:
        c.execute(
            "INSERT INTO players(guild_id,nick,uid,lvl,rank,kd,wr,created_by,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (gid, nick, uid, lvl, rank, kd, wr, by, datetime.now(timezone.utc).isoformat()),
        )

def get_players(gid, only_fav=False, search=None):
    q = "SELECT * FROM players WHERE guild_id=?"
    args = [gid]
    if only_fav:
        q += " AND fav=1"
    if search:
        q += " AND (nick LIKE ? OR uid LIKE ?)"
        args += [f"%{search}%", f"%{search}%"]
    q += " ORDER BY fav DESC, kd DESC LIMIT 25"
    with con() as c:
        return c.execute(q, args).fetchall()

def get_player(pid, gid):
    with con() as c:
        return c.execute(
            "SELECT * FROM players WHERE id=? AND guild_id=?", (pid, gid)
        ).fetchone()

def delete_player(pid, gid):
    with con() as c:
        c.execute("DELETE FROM players WHERE id=? AND guild_id=?", (pid, gid))

def toggle_fav(pid, gid):
    with con() as c:
        c.execute("UPDATE players SET fav = 1 - fav WHERE id=? AND guild_id=?", (pid, gid))
        row = c.execute("SELECT fav FROM players WHERE id=? AND guild_id=?", (pid, gid)).fetchone()
        return row[0] if row else 0

def guild_stats(gid):
    with con() as c:
        return c.execute(
            "SELECT COUNT(*) n, AVG(kd) kd, AVG(wr) wr, MAX(kd) top FROM players WHERE guild_id=?",
            (gid,),
        ).fetchone()

def player_embed(p: sqlite3.Row) -> d.Embed:
    e = d.Embed(
        title=f"{'★ ' if p['fav'] else ''}{p['nick']}",
        color=RANK_COLOR.get(p["rank"], 0xFF6A00),
    )
    e.add_field(name="ID", value=p["uid"], inline=True)
    e.add_field(name="Nivel", value=p["lvl"], inline=True)
    e.add_field(name="Rango", value=p["rank"], inline=True)
    e.add_field(name="K/D", value=f"{p['kd']:.2f}", inline=True)
    e.add_field(name="Winrate", value=f"{p['wr']}%", inline=True)
    e.set_footer(text=f"Registro #{p['id']}")
    return e

def list_embed(rows, title) -> d.Embed:
    e = d.Embed(title=title, color=0xFF6A00)
    if not rows:
        e.description = "No hay jugadores registrados todavía."
        return e
    e.description = "\n".join(
        f"`#{p['id']}` {'★' if p['fav'] else ''}**{p['nick']}** · ID {p['uid']}"
        f" · {p['rank']} · K/D {p['kd']:.2f} · WR {p['wr']}%"
        for p in rows
    )
    e.set_footer(text=f"{len(rows)} jugador(es) mostrados")
    return e

def stats_embed(s) -> d.Embed:
    e = d.Embed(title="Estadísticas de la escuadra", color=0xFFA500)
    e.add_field(name="Jugadores", value=s["n"] or 0)
    e.add_field(name="K/D medio", value=f"{s['kd'] or 0:.2f}")
    e.add_field(name="Winrate medio", value=f"{s['wr'] or 0:.0f}%")
    e.add_field(name="Mejor K/D", value=f"{s['top'] or 0:.2f}")
    return e

class AddPlayerModal(d.ui.Modal, title="Nuevo jugador"):
    nick = d.ui.TextInput(label="Nickname", max_length=18)
    uid = d.ui.TextInput(label="ID", max_length=12)
    lvl = d.ui.TextInput(label="Nivel (1-100)", default="1", max_length=3)
    kd = d.ui.TextInput(label="K/D", default="1.00", max_length=5)
    wr = d.ui.TextInput(label="Winrate % (0-100)", default="0", max_length=3)

    def __init__(self, rank: str = "Bronce"):
        super().__init__()
        self.rank = rank

    async def on_submit(self, it: d.Interaction):
        def num(v, cast, default):
            try:
                return cast(v)
            except ValueError:
                return default
        add_player(
            it.guild_id, self.nick.value.strip(), self.uid.value.strip(),
            max(1, min(100, num(self.lvl.value, int, 1))), self.rank,
            max(0.0, num(self.kd.value, float, 0.0)),
            max(0, min(100, num(self.wr.value, int, 0))),
            it.user.id,
        )
        await it.response.send_message(
            f"Jugador **{self.nick.value}** añadido en {self.rank}.", ephemeral=True
        )

class RankSelect(d.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Elige el rango del jugador", options=[
            d.SelectOption(label=r) for r in RANKS
        ])
    async def callback(self, it: d.Interaction):
        await it.response.send_modal(AddPlayerModal(self.values[0]))

class RankView(d.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(RankSelect())

class DeleteSelect(d.ui.Select):
    def __init__(self, rows):
        super().__init__(placeholder="Selecciona jugador(es) a borrar",
                         max_values=min(len(rows), 25),
                         options=[
                             d.SelectOption(
                                 label=f"{p['nick']} — ID {p['uid']}",
                                 value=str(p["id"]), description=p["rank"],
                             ) for p in rows
                         ])
    async def callback(self, it: d.Interaction):
        for pid in self.values:
            delete_player(int(pid), it.guild_id)
        await it.response.edit_message(
            content=f"Eliminados {len(self.values)} jugador(es).", embed=None, view=None
        )

class PanelView(d.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @d.ui.button(label="Añadir", emoji="➕", style=d.ButtonStyle.success, custom_id="ff:add")
    async def add(self, it: d.Interaction, _):
        await it.response.send_message("Elige el rango:", view=RankView(), ephemeral=True)

    @d.ui.button(label="Lista", emoji="📋", style=d.ButtonStyle.primary, custom_id="ff:list")
    async def lst(self, it: d.Interaction, _):
        rows = get_players(it.guild_id)
        await it.response.send_message(embed=list_embed(rows, "Escuadra"), ephemeral=True)

    @d.ui.button(label="Favoritos", emoji="★", style=d.ButtonStyle.secondary, custom_id="ff:fav")
    async def favs(self, it: d.Interaction, _):
        rows = get_players(it.guild_id, only_fav=True)
        await it.response.send_message(embed=list_embed(rows, "Favoritos"), ephemeral=True)

    @d.ui.button(label="Estadísticas", emoji="📊", style=d.ButtonStyle.secondary, custom_id="ff:stats")
    async def stats(self, it: d.Interaction, _):
        await it.response.send_message(embed=stats_embed(guild_stats(it.guild_id)), ephemeral=True)

    @d.ui.button(label="Borrar", emoji="🗑", style=d.ButtonStyle.danger, custom_id="ff:del")
    async def delete(self, it: d.Interaction, _):
        rows = get_players(it.guild_id)
        if not rows:
            return await it.response.send_message("No hay jugadores.", ephemeral=True)
        v = d.ui.View(timeout=120)
        v.add_item(DeleteSelect(rows))
        await it.response.send_message("Selecciona a quién borrar:", view=v, ephemeral=True)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=d.Intents.default())
    async def setup_hook(self):
        init_db()
        self.add_view(PanelView())
        if GUILD_ID:
            g = d.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)
        else:
            await self.tree.sync()
    async def on_ready(self):
        print(f"Conectado como {self.user} ({self.user.id})")

bot = Bot()

@bot.tree.command(name="panel", description="Publica el panel de la escuadra")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel(it: d.Interaction):
    e = d.Embed(title="FF PANEL", description="Gestión de escuadra.\nUsa los botones de abajo.", color=0xFF6A00)
    e.set_footer(text="Datos guardados en la base del servidor")
    await it.response.send_message(embed=e, view=PanelView())

@bot.tree.command(name="buscar", description="Busca un jugador por nick o ID")
@app_commands.describe(q="Nickname o ID")
async def buscar(it: d.Interaction, q: str):
    rows = get_players(it.guild_id, search=q)
    await it.response.send_message(embed=list_embed(rows, f"Resultados: {q}"), ephemeral=True)

@bot.tree.command(name="favorito", description="Marca o desmarca un jugador como favorito")
@app_commands.describe(pid="Número de registro (#id)")
async def favorito(it: d.Interaction, pid: int):
    if not get_player(pid, it.guild_id):
        return await it.response.send_message("Ese registro no existe.", ephemeral=True)
    state = toggle_fav(pid, it.guild_id)
    await it.response.send_message("Marcado como favorito ★" if state else "Favorito quitado", ephemeral=True)

@bot.tree.command(name="borrar", description="Borra un jugador por número de registro")
@app_commands.describe(pid="Número de registro (#id)")
async def borrar(it: d.Interaction, pid: int):
    if not get_player(pid, it.guild_id):
        return await it.response.send_message("Ese registro no existe.", ephemeral=True)
    delete_player(pid, it.guild_id)
    await it.response.send_message(f"Registro #{pid} eliminado.", ephemeral=True)

@bot.tree.command(name="exportar", description="Exporta la escuadra en CSV")
async def exportar(it: d.Interaction):
    rows = get_players(it.guild_id)
    if not rows:
        return await it.response.send_message("Nada que exportar.", ephemeral=True)
    lines = ["nick,uid,lvl,rank,kd,wr,fav"]
    lines += [f"{p['nick']},{p['uid']},{p['lvl']},{p['rank']},{p['kd']},{p['wr']},{p['fav']}" for p in rows]
    data = "\n".join(lines).encode()
    await it.response.send_message(file=d.File(io.BytesIO(data), "escuadra.csv"), ephemeral=True)

if __name__ == "__main__":
    if not TOKEN:
        print("FALTA TOKEN en .env")
    else:
        bot.run(TOKEN)
