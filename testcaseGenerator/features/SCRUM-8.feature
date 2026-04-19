# Feature: Validate the checkout functionality

## Background:
Given User is logged into the system
And User has items in the shopping cart

## Scenario: Verify checkout page loads successfully
When User navigates to the checkout page
Then The checkout page should display
And All cart items should be visible
And Checkout form should be displayed

## Scenario: Verify shipping address entry
Given User is on the checkout page
When User enters valid shipping address
And User enters valid city
And User enters valid state
And User enters valid postal code
Then Shipping address should be saved
And Address validation message should confirm

## Scenario: Verify payment method selection
Given User is on the checkout page with address filled
When User selects payment method
And User enters valid payment details
Then Payment method should be selected
And Payment details should be validated

## Scenario: Verify order summary before submission
Given User has completed address and payment details
When User reviews the order summary
Then Order total should display correctly
And Shipping cost should be calculated
And Tax should be applied
And All line items should be listed

## Scenario: Verify successful order placement
Given User has completed all checkout fields
When User clicks the place order button
Then Order should be processed successfully
And Order confirmation page should display
And Confirmation number should be generated
And Order confirmation email should be sent

## Scenario: Verify checkout with promo code
Given User is on the checkout page
When User enters valid promo code
And User clicks apply button
Then Discount should be applied to order total
And Updated total should display

## Scenario: Verify checkout error handling
Given User is on the checkout page
When User enters invalid payment details
And User clicks place order button
Then Error message should display
And Order should not be processed