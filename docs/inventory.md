# Inventory and sales

## Overview

**Stock Management** keeps a school catalogue of product categories and products, including sale price and quantity. AXIS can record products sold while collecting a student's fees, or let an administrator search for a student and continue to that student's collection page.

## Create a category

1. Open **Stock Management**.
2. Choose **Add Category**.
3. Enter a clear category name and optional description, then save.
4. Confirm that the category appears in the list.

## Add or update a product

1. From Stock Management, choose **Add Product**.
2. Choose its category and enter the product name, selling price, and starting quantity.
3. Add optional notes and save.
4. Open the product detail page to review current stock, sales totals, and recent buyers.
5. To update product information or the on-hand quantity, use the edit action and save the corrected value.

AXIS generates a SKU when a new product is saved without one. Stock is reduced automatically when an item is included in a saved student fee-collection transaction.

## Sell an item

### During fee collection

1. Open **Fee Collection** and select the student.
2. Choose **Add Items**.
3. Search by name or filter by category.
4. Add the product and quantity. AXIS shows the available stock and calculates the item total.
5. Choose **Done**, enter the amount received, and review the fee and item totals.
6. Choose **Process Payment** and confirm the receipt.

### From Sell Separately

1. Open **Sell Separately** from the school navigation or mobile **More** area.
2. Search for a student or filter by grade/section.
3. Select the student to continue to the fee-collection screen and include the product there.

!!! note "Sale requires a student collection"
    The separate-sell page finds a student and routes you into fee collection. It is not an anonymous point-of-sale checkout; the sale is recorded against a student's payment.

## Review stock

The Stock Management page shows categories, products, total stock value, low-stock count, and recent item sales. A product detail page shows its sales history and current on-hand value. Products with fewer than 10 units are counted as low stock in the overview.

```text
Stock Management
[Categories] [Products] [Low stock] [Recent sales]
Category    Product             Price      On hand     [Details]
Uniforms    Sports uniform      amount    quantity
```

## Desktop and mobile

=== "Desktop"

    Use the stock table and product detail page for more history. Add/edit forms may open as a modal from the stock page.

=== "Mobile"

    Tap **Stock** in the bottom menu or open **More**. Product lists, category filtering, and product detail are available in a compact layout.

## Common scenarios

- **A new shipment arrives:** Edit the product's quantity to the new on-hand amount and save.
- **Stock is running low:** Open the product details and arrange replenishment before processing more sales.
- **An item is sold with a fee payment:** Add it in the collection drawer, confirm the correct quantity, then check the receipt and stock count.
- **A category is no longer needed:** Delete it only after every product has been moved or removed. AXIS blocks deleting a category that still contains products.

!!! warning "Check quantity before saving"
    AXIS checks that enough stock exists for the requested item quantity. Verify the selected product and quantity before processing the payment; stock is reduced when the payment saves.

## FAQ

### Why can't I delete a category?
A category cannot be deleted while it still has products. Reassign or remove the products first.

### Why did stock decrease?
A product sale included in a saved payment reduces the on-hand quantity. Review the receipt and product sales history.

### Does deleting a product erase its sales history?
Product details are used by sales records, but product deletion can remove the live catalogue entry. Ask the administrator before deleting a product that has sales history; prefer updating its quantity or notes when possible.

### Is the stock value the same as cash collected?
No. Stock value is based on product selling price multiplied by current quantity. Sales totals are separate from the remaining inventory value.

## Troubleshooting

| Problem | What to do |
|---|---|
| Product is missing from the collection drawer | Confirm the product exists, has a category, and its stock quantity is above zero. |
| Quantity is too low | Update the stock count after checking the physical inventory; do not enter a larger quantity just to bypass the warning. |
| Product does not appear in its category | Confirm the product's category assignment and clear search/category filters. |
| Category deletion is blocked | Move or delete linked products first, then try again. |
| Sale receipt is missing | Search the student's payments in Reports or their profile; confirm whether the transaction was saved before trying again. |

## Related guides

[Fees and vouchers](fees.md) · [Reports](reports.md) · [Students](students.md)
