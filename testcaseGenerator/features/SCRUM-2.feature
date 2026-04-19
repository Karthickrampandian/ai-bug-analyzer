
Feature: Validate user login functionality

  Background:
    Given I navigate to the login page

  Scenario: Successful login with valid credentials
    When I enter valid username
    And I enter valid password
    And I click on login button
    Then I should be logged in successfully
    And I should be redirected to the home page

  Scenario: Login failure with invalid username
    When I enter invalid username
    And I enter valid password
    And I click on login button
    Then I should see an error message
    And I should remain on the login page

  Scenario: Login failure with invalid password
    When I enter valid username
    And I enter invalid password
    And I click on login button
    Then I should see an error message
    And I should remain on the login page

  Scenario: Login failure with invalid credentials
    When I enter invalid username
    And I enter invalid password
    And I click on login button
    Then I should see an error message
    And I should remain on the login page

  Scenario: Login with empty username field
    When I leave username field empty
    And I enter valid password
    And I click on login button
    Then I should see a validation error
    And I should remain on the login page

  Scenario: Login with empty password field
    When I enter valid username
    And I leave password field empty
    And I click on login button
    Then I should see a validation error
    And I should remain on the login page

  Scenario: Login with empty credentials
    When I leave username field empty
    And I leave password field empty
    And I click on login button
    Then I should see validation errors
    And I should remain on the login page
