import csv
import json
import io
from typing import List, Dict, Any, Optional
import logging
from ..models import Product, Category, Occasion, Season, ProductAttribute

logger = logging.getLogger(__name__)

class DataLoader:
    
    def load_sample_products(self) -> List[Product]:
        sample_products = [
            {
                "product_id": "SKU001",
                "name": "Classic White Cotton T-Shirt",
                "category": Category.TOPS,
                "description": "Essential white cotton t-shirt with a relaxed fit. Perfect for layering or wearing on its own. Made from 100% organic cotton for ultimate comfort.",
                "price": 29.99,
                "attributes": {
                    "color": ["white"],
                    "material": "cotton",
                    "occasion": [Occasion.CASUAL],
                    "season": [Season.ALL_SEASON],
                    "style": "classic",
                    "brand": "Basics Co"
                }
            },
            {
                "product_id": "SKU002",
                "name": "High-Waisted Black Denim Jeans",
                "category": Category.BOTTOMS,
                "description": "Timeless high-waisted black denim jeans with a slim fit through the legs. Features stretch denim for comfort and movement.",
                "price": 89.99,
                "attributes": {
                    "color": ["black"],
                    "material": "denim",
                    "occasion": [Occasion.CASUAL, Occasion.WORK],
                    "season": [Season.ALL_SEASON],
                    "style": "modern",
                    "brand": "DenimCraft"
                }
            },
            {
                "product_id": "SKU003",
                "name": "Silk Midi Wrap Dress",
                "category": Category.DRESSES,
                "description": "Elegant silk midi dress with a flattering wrap silhouette. Features a V-neckline and flutter sleeves. Perfect for special occasions.",
                "price": 249.99,
                "sale_price": 199.99,
                "attributes": {
                    "color": ["navy", "burgundy"],
                    "material": "silk",
                    "occasion": [Occasion.COCKTAIL, Occasion.FORMAL],
                    "season": [Season.SPRING, Season.SUMMER],
                    "style": "elegant",
                    "brand": "Luxe Studio"
                }
            },
            {
                "product_id": "SKU004",
                "name": "Leather Bomber Jacket",
                "category": Category.OUTERWEAR,
                "description": "Classic leather bomber jacket with ribbed cuffs and hem. Features multiple pockets and a smooth zip closure.",
                "price": 399.99,
                "attributes": {
                    "color": ["black", "brown"],
                    "material": "leather",
                    "occasion": [Occasion.CASUAL],
                    "season": [Season.FALL, Season.WINTER],
                    "style": "edgy",
                    "brand": "Urban Edge"
                }
            },
            {
                "product_id": "SKU005",
                "name": "Canvas Low-Top Sneakers",
                "category": Category.SHOES,
                "description": "Comfortable canvas low-top sneakers with rubber sole. Classic design that pairs well with any casual outfit.",
                "price": 59.99,
                "attributes": {
                    "color": ["white", "black", "navy"],
                    "material": "canvas",
                    "occasion": [Occasion.CASUAL, Occasion.ATHLETIC],
                    "season": [Season.ALL_SEASON],
                    "style": "sporty",
                    "brand": "StepForward"
                }
            },
            {
                "product_id": "SKU006",
                "name": "Cashmere Knit Sweater",
                "category": Category.TOPS,
                "description": "Luxurious cashmere sweater with a relaxed fit. Features ribbed cuffs and hem for a polished look.",
                "price": 189.99,
                "attributes": {
                    "color": ["camel", "grey", "cream"],
                    "material": "cashmere",
                    "occasion": [Occasion.CASUAL, Occasion.WORK],
                    "season": [Season.FALL, Season.WINTER],
                    "style": "classic",
                    "brand": "Cozy Luxe"
                }
            },
            {
                "product_id": "SKU007",
                "name": "Pleated Midi Skirt",
                "category": Category.BOTTOMS,
                "description": "Flowy pleated midi skirt with elastic waistband. Perfect for creating feminine, sophisticated looks.",
                "price": 79.99,
                "attributes": {
                    "color": ["blush", "black", "navy"],
                    "material": "polyester",
                    "occasion": [Occasion.WORK, Occasion.COCKTAIL],
                    "season": [Season.SPRING, Season.SUMMER],
                    "style": "feminine",
                    "brand": "Femme Fashion"
                }
            },
            {
                "product_id": "SKU008",
                "name": "Leather Crossbody Bag",
                "category": Category.BAGS,
                "description": "Compact leather crossbody bag with adjustable strap. Features multiple compartments for organization.",
                "price": 149.99,
                "attributes": {
                    "color": ["tan", "black"],
                    "material": "leather",
                    "occasion": [Occasion.CASUAL, Occasion.WORK],
                    "season": [Season.ALL_SEASON],
                    "style": "minimalist",
                    "brand": "Bag Studio"
                }
            },
            {
                "product_id": "SKU009",
                "name": "Gold Layered Necklace Set",
                "category": Category.JEWELRY,
                "description": "Set of three delicate gold-plated necklaces in varying lengths. Perfect for layering or wearing separately.",
                "price": 49.99,
                "attributes": {
                    "color": ["gold"],
                    "material": "gold-plated",
                    "occasion": [Occasion.CASUAL, Occasion.COCKTAIL],
                    "season": [Season.ALL_SEASON],
                    "style": "trendy",
                    "brand": "Shine Jewelry"
                }
            },
            {
                "product_id": "SKU010",
                "name": "Linen Button-Up Shirt",
                "category": Category.TOPS,
                "description": "Breathable linen button-up shirt with a relaxed fit. Perfect for warm weather and beach vacations.",
                "price": 69.99,
                "attributes": {
                    "color": ["white", "light blue", "beige"],
                    "material": "linen",
                    "occasion": [Occasion.CASUAL, Occasion.BEACH],
                    "season": [Season.SUMMER],
                    "style": "relaxed",
                    "brand": "Summer Breeze"
                }
            }
        ]
        
        products = []
        for data in sample_products:
            try:
                attributes = ProductAttribute(**data["attributes"])
                product = Product(
                    product_id=data["product_id"],
                    name=data["name"],
                    category=data["category"],
                    description=data["description"],
                    attributes=attributes,
                    price=data["price"],
                    sale_price=data.get("sale_price"),
                    sizes=["XS", "S", "M", "L", "XL"],
                    in_stock=True,
                    images=[f"https://placeholder.com/{data['product_id']}.jpg"]
                )
                products.append(product)
            except Exception as e:
                logger.error(f"Error creating product {data.get('product_id')}: {e}")
        
        return products
    
    async def process_csv_upload(self, csv_content: bytes, vector_store: Any) -> int:
        try:
            csv_text = csv_content.decode('utf-8')
            csv_file = io.StringIO(csv_text)
            reader = csv.DictReader(csv_file)
            
            products = []
            for row in reader:
                product = self._parse_csv_row(row)
                if product:
                    products.append(product)
            
            if products:
                return await vector_store.add_products_batch(products)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return 0
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Optional[Product]:
        try:
            category_map = {
                "top": Category.TOPS,
                "tops": Category.TOPS,
                "bottom": Category.BOTTOMS,
                "bottoms": Category.BOTTOMS,
                "dress": Category.DRESSES,
                "dresses": Category.DRESSES,
                "outerwear": Category.OUTERWEAR,
                "shoes": Category.SHOES,
                "accessories": Category.ACCESSORIES,
                "bags": Category.BAGS,
                "jewelry": Category.JEWELRY
            }
            
            category_str = row.get("category", "tops").lower()
            category = category_map.get(category_str, Category.TOPS)
            
            colors = [c.strip() for c in row.get("colors", "").split(",") if c.strip()]
            
            occasions = []
            if row.get("occasions"):
                for occ in row["occasions"].split(","):
                    occ_clean = occ.strip().lower()
                    try:
                        occasions.append(Occasion(occ_clean))
                    except:
                        pass
            
            seasons = []
            if row.get("seasons"):
                for season in row["seasons"].split(","):
                    season_clean = season.strip().lower()
                    try:
                        seasons.append(Season(season_clean))
                    except:
                        pass
            
            attributes = ProductAttribute(
                color=colors,
                material=row.get("material"),
                occasion=occasions,
                season=seasons,
                style=row.get("style"),
                brand=row.get("brand")
            )
            
            sizes = [s.strip() for s in row.get("sizes", "").split(",") if s.strip()]
            if not sizes:
                sizes = ["S", "M", "L"]
            
            product = Product(
                product_id=row.get("product_id", row.get("sku", "")),
                name=row.get("name", row.get("product_name", "")),
                category=category,
                description=row.get("description", ""),
                attributes=attributes,
                price=float(row.get("price", 0)),
                sale_price=float(row.get("sale_price")) if row.get("sale_price") else None,
                sizes=sizes,
                in_stock=row.get("in_stock", "true").lower() == "true",
                images=[row.get("image_url")] if row.get("image_url") else []
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return None
    
    def export_products_to_csv(self, products: List[Product]) -> str:
        output = io.StringIO()
        
        fieldnames = [
            "product_id", "name", "category", "description", "price", 
            "sale_price", "colors", "material", "occasions", "seasons",
            "style", "brand", "sizes", "in_stock", "image_url"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for product in products:
            row = {
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category.value,
                "description": product.description,
                "price": product.price,
                "sale_price": product.sale_price or "",
                "colors": ",".join(product.attributes.color) if product.attributes.color else "",
                "material": product.attributes.material or "",
                "occasions": ",".join([o.value for o in product.attributes.occasion]) if product.attributes.occasion else "",
                "seasons": ",".join([s.value for s in product.attributes.season]) if product.attributes.season else "",
                "style": product.attributes.style or "",
                "brand": product.attributes.brand or "",
                "sizes": ",".join(product.sizes) if product.sizes else "",
                "in_stock": str(product.in_stock).lower(),
                "image_url": product.images[0] if product.images else ""
            }
            writer.writerow(row)
        
        return output.getvalue()