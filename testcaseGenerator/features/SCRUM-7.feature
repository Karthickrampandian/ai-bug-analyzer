
Feature: Remove items from shopping cart

Background:
  Given I am logged into the system
  And I have navigated to the shopping cart

Scenario: Remove single item from cart
  Given I have one item in the cart
  When I click the remove button for that item
  Then the item is removed from the cart
  And the cart is now empty
  And a confirmation message is displayed

Scenario: Remove one item when multiple items exist in cart
  Given I have multiple items in the cart
  When I click the remove button for one specific item
  Then that item is removed from the cart
  And the remaining items are still displayed
  And the cart total is updated

Scenario: Remove all items from cart one by one
  Given I have multiple items in the cart
  When I remove each item individually
  Then all items are removed from the cart
  And the cart becomes empty
  And an empty cart message is displayed

Scenario: Cancel item removal
  Given I have items in the cart
  When I click the remove button for an item
  And I cancel the removal action
  Then the item remains in the cart
  And no changes are made to the cart

Scenario: Verify cart total updates after removal
  Given I have items with prices in the cart
  And the initial cart total is calculated
  When I remove an item from the cart
  Then the cart total is recalculated
  And the new total reflects the removed item price
