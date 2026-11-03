#!/usr/bin/env python3
"""Build the agent-readable catalog layer from products-source.json.

Rerunnable: python3 build_catalog.py
Outputs (all local, nothing deployed):
  catalog.json                 UCP Catalog-shaped full catalog
  products/<id>.jsonld.json    schema.org Product JSON-LD per product
  llms.txt / agents.md         agent guidance for the whole store
  .well-known/ucp              UCP profile declaration (honest: checkout is an external human link)
  sitemap.xml                  planned-base sitemap (rebase at deploy time)
  index.html                   human-readable catalog preview with embedded JSON-LD graph
"""
import json, os, html
from xml.sax.saxutils import escape as xesc

HERE = os.path.dirname(os.path.abspath(__file__))
PLANNED_BASE = "https://binbin7418-dotcom.github.io/agent-catalog/"  # placeholder until deploy; rebase then

src = json.load(open(os.path.join(HERE, "products-source.json"), encoding="utf-8"))
products = src["products"]
seller = src["seller"]


def money(m):
    return {"amount": m["amount_minor"], "currency": m["currency"]}


def price_range(p):
    amounts = [v["price"]["amount_minor"] for v in p["variants"]] or [p["price"]["amount_minor"]]
    return {"min": {"amount": min(amounts), "currency": "USD"},
            "max": {"amount": max(amounts), "currency": "USD"}}


def return_policy_ld(rp):
    return {
        "@type": "MerchantReturnPolicy",
        "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
        "merchantReturnDays": rp["merchant_return_days"],
        "refundType": "https://schema.org/FullRefund",
        "description": rp["text"],
    }


def product_jsonld(p):
    buy = p["buy_urls"].get("gumroad") or p["buy_urls"].get("gumroad_explainer") or next(iter(p["buy_urls"].values()), "")
    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["title"],
        "description": p["description_full"],
        "sku": p.get("sku_gumroad") or p["id"],
        "category": p["category"],
        "brand": {"@type": "Brand", "name": seller["brand"]},
        "offers": {
            "@type": "Offer",
            "price": round(p["price"]["amount_minor"] / 100, 2),
            "priceCurrency": p["price"]["currency"],
            "availability": "https://schema.org/InStock",
            "url": buy,
        },
        "hasMerchantReturnPolicy": return_policy_ld(p["return_policy"]),
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "delivery", "value": p["description_facts"]["delivery"]},
            {"@type": "PropertyValue", "name": "file_format", "value": p["description_facts"]["file_format"]},
            {"@type": "PropertyValue", "name": "requirements", "value": p["description_facts"]["requirements"]},
        ],
    }
    if p.get("image"):
        ld["image"] = p["image"]
    if len(p["variants"]) > 1:
        ld["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": round(price_range(p)["min"]["amount"] / 100, 2),
            "highPrice": round(price_range(p)["max"]["amount"] / 100, 2),
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": buy,
            "offerCount": len(p["variants"]),
        }
    return ld


# ---- catalog.json (UCP shape) ----
catalog_products = []
for p in products:
    catalog_products.append({
        "id": p["id"],
        "title": p["title"],
        "description": p["description_facts"]["what_it_does"],
        "description_full": p["description_full"],
        "price_range": price_range(p),
        "variants": [{
            "id": v["id"], "title": v["title"], "description": v["description"],
            "price": money(v["price"]), "availability": v["availability"],
            "buy_url": v.get("buy_url", ""),
        } for v in p["variants"]],
        "availability": p["availability"],
        "category": p["category"],
        "sku": p.get("sku_gumroad") or "",
        "image": p.get("image", ""),
        "delivery": p["description_facts"]["delivery"],
        "file_format": p["description_facts"]["file_format"],
        "requirements": p["description_facts"]["requirements"],
        "whats_inside": p["description_facts"]["whats_inside"],
        "return_policy": p["return_policy"],
        "seller": {"name": seller["name"], "brand": seller["brand"],
                   "support_email": seller["support_email"]},
        "buy_urls": p["buy_urls"],
        "landing_url": p.get("landing_url", ""),
    })

catalog = {
    "ucp_version": "2026-04-08",
    "generated_at": src["generated_at"],
    "seller": seller,
    "checkout": {
        "mode": "external_link",
        "note": "There is no machine checkout endpoint. Present the buy_url to the human buyer; "
                "checkout completes on Gumroad or Payhip (card / PayPal).",
    },
    "catalog": {"products": catalog_products},
}
json.dump(catalog, open(os.path.join(HERE, "catalog.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

# ---- per-product JSON-LD ----
os.makedirs(os.path.join(HERE, "products"), exist_ok=True)
for p in products:
    json.dump(product_jsonld(p),
              open(os.path.join(HERE, "products", p["id"] + ".jsonld.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

# ---- .well-known/ucp ----
os.makedirs(os.path.join(HERE, ".well-known"), exist_ok=True)
ucp = {
    "version": "2026-04-08",
    "seller": {"name": seller["name"], "brand": seller["brand"],
               "support_email": seller["support_email"]},
    "services": {"catalog": {"url": "catalog.json", "format": "UCP Catalog (JSON)"}},
    "capabilities": ["catalog.search", "catalog.lookup"],
    "checkout": {
        "mode": "external_link",
        "handlers": ["gumroad", "payhip"],
        "note": "No machine checkout endpoint exists. Hand the human buyer the product buy_url; "
                "payment completes on Gumroad or Payhip.",
    },
    "files": {"llms": "llms.txt", "agents": "agents.md", "sitemap": "sitemap.xml"},
}
json.dump(ucp, open(os.path.join(HERE, ".well-known", "ucp"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

# ---- llms.txt & agents.md ----
cats = {}
for p in products:
    cats.setdefault(p["category"], []).append(p)

def agent_doc(title):
    lines = [f"# {title}", "",
             f"Seller: {seller['name']} (brand: {seller['brand']}). Support: {seller['support_email']}.",
             "All prices are one-time payments in USD. No subscriptions unless a product page says so.",
             "",
             "## How to buy (for agents)",
             "1. Find the product in catalog.json and read its structured facts: price, delivery, file_format, requirements, return_policy.",
             "2. Present the matching buy_urls link to the human buyer. Checkout is completed by the human on Gumroad or Payhip (card / PayPal). There is no machine checkout endpoint - do not claim you can purchase directly.",
             "3. Digital tools and n8n packs are delivered as an instant download right after checkout. PitchReel is a service: the film is produced after the buyer locks a script on the PitchReel site. The website monitoring service is delivered by email over 90 days.",
             "",
             "## Refund policy (summary; per-product text is in catalog.json)",
             "- Software tools, puzzle/worksheet generators and n8n packs: if the product will not run on the buyer's machine, we fix it first; if we cannot make it work, full refund within 30 days.",
             "- Website monitoring service: full refund any time in the first 30 days.",
             "- PitchReel videos: our mistakes are fixed and re-rendered free; if unfixable, full refund. Cancellation before production starts is refunded in full.",
             f"Support for everything: {seller['support_email']} (answered within one business day).",
             "",
             "## Catalog by category", ""]
    for cat in sorted(cats):
        items = cats[cat]
        lo = min(price_range(p)["min"]["amount"] for p in items) / 100
        hi = max(price_range(p)["max"]["amount"] for p in items) / 100
        lines.append(f"- {cat}: {len(items)} product(s), ${lo:.0f}-${hi:.0f}")
    lines += ["", "## Products", ""]
    for p in products:
        pr = price_range(p)
        price = f"${pr['min']['amount']/100:.0f}" if pr["min"] == pr["max"] else f"${pr['min']['amount']/100:.0f}-${pr['max']['amount']/100:.0f}"
        buy = p["buy_urls"].get("gumroad") or next(iter(p["buy_urls"].values()), "")
        lines.append(f"- [{p['category']}] {p['title']} - {price} USD - buy: {buy}")
    lines.append("")
    return "\n".join(lines)

open(os.path.join(HERE, "llms.txt"), "w", encoding="utf-8").write(agent_doc("Bin Bin / Vision - product catalog for AI agents"))
open(os.path.join(HERE, "agents.md"), "w", encoding="utf-8").write(agent_doc("Agent guidance - Bin Bin / Vision store"))

# ---- sitemap.xml (planned base; rebase at deploy) ----
urls = [PLANNED_BASE, PLANNED_BASE + "catalog.json", PLANNED_BASE + "llms.txt", PLANNED_BASE + "agents.md"]
urls += [PLANNED_BASE + "products/" + p["id"] + ".jsonld.json" for p in products]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      "<!-- Planned base URL placeholder; rebase to the real catalog domain at deploy time. -->",
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append(f"  <url><loc>{xesc(u)}</loc></url>")
sm.append("</urlset>")
open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")

# ---- index.html ----
rows = []
graph = []
for p in products:
    graph.append(product_jsonld(p))
    pr = price_range(p)
    price = f"${pr['min']['amount']/100:.2f}" if pr["min"] == pr["max"] else f"${pr['min']['amount']/100:.2f} - ${pr['max']['amount']/100:.2f}"
    buy = p["buy_urls"].get("gumroad") or next(iter(p["buy_urls"].values()), "")
    rows.append(f"<tr><td>{html.escape(p['category'])}</td><td>{html.escape(p['title'])}</td>"
                f"<td>{price} USD</td><td><a href=\"{html.escape(buy)}\">Buy</a></td>"
                f"<td><a href=\"products/{p['id']}.jsonld.json\">JSON-LD</a></td></tr>")
index = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Bin Bin / Vision - Product Catalog (agent-readable)</title>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)}</script>
</head><body>
<h1>Product Catalog - Bin Bin (Vision)</h1>
<p>{len(products)} products. Machine-readable: <a href="catalog.json">catalog.json</a> (UCP shape),
<a href="llms.txt">llms.txt</a>, <a href="agents.md">agents.md</a>, <a href=".well-known/ucp">.well-known/ucp</a>.
Support: {seller['support_email']}. Checkout completes on Gumroad or Payhip.</p>
<table border="1" cellspacing="0" cellpadding="6">
<tr><th>Category</th><th>Product</th><th>Price</th><th>Buy</th><th>Structured data</th></tr>
{''.join(rows)}
</table>
</body></html>
"""
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(index)

print(f"products={len(products)}")
print(f"jsonld_files={len(products)}")
print(f"with_image={sum(1 for p in products if p.get('image'))}")
print(f"with_landing={sum(1 for p in products if p.get('landing_url'))}")
print(f"with_payhip={sum(1 for p in products if 'payhip' in p['buy_urls'])}")
print(f"with_whats_inside={sum(1 for p in products if p['description_facts']['whats_inside'])}")
print("files: catalog.json, products/*.jsonld.json, llms.txt, agents.md, .well-known/ucp, sitemap.xml, index.html")
