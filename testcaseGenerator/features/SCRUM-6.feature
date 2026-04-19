
Feature: Add items to inventory

Background:
  Given I am logged into the system
  And I have access to the inventory management module

Scenario: Add a new item to inventory with all required fields
  Given I navigate to the inventory management module
  When I click on "Add Item" button
  And I enter the item code
  And I enter the item name
  And I enter the item description
  And I select the item category
  And I enter the unit price
  And I enter the quantity in stock
  And I enter the reorder level
  And I click the "Save" button
  Then the item should be successfully added to inventory
  And a confirmation message should be displayed
  And the new item should appear in the inventory list

Scenario: Add multiple items to inventory in batch
  Given I navigate to the inventory management module
  When I click on "Bulk Add Items" option
  And I upload a valid inventory file with multiple items
  And I verify all items from the file are listed for review
  And I click the "Confirm" button
  Then all items should be successfully added to inventory
  And a summary report should display the number of items added

Scenario: Prevent adding duplicate items to inventory
  Given I navigate to the inventory management module
  And an item with code "ITEM001" already exists in inventory
  When I click on "Add Item" button
  And I enter the item code "ITEM001"
  And I enter other required item details
  And I click the "Save" button
  Then an error message should be displayed indicating duplicate item code
  And the item should not be added to inventory

Scenario: Add item to inventory with optional fields
  Given I navigate to the inventory management module
  When I click on "Add Item" button
  And I enter all mandatory fields
  And I enter optional fields like supplier details and lead time
  And I click the "Save" button
  Then the item should be successfully added with optional information
  And the item details should be stored correctly in the system

Scenario: Validate required fields when adding items
  Given I navigate to the inventory management module
  When I click on "Add Item" button
  And I leave the mandatory item code field empty
  And I click the "Save" button
  Then a validation error should be displayed for the missing field
  And the item should not be added to inventory
