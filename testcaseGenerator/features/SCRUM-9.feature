
Feature: Validate logout functionality

Background:
  Given I am logged into the system

Scenario: Verify successful logout from the application
  When I click on the logout button
  Then I should be redirected to the login page
  And the session should be terminated
  And I should not be able to access protected pages without re-authentication

Scenario: Verify logout clears user session data
  When I click on the logout button
  Then all user session data should be cleared
  And cached credentials should be removed
  And I should be returned to the login page

Scenario: Verify logout from different pages
  Given I am on the dashboard page
  When I click on the logout button
  Then I should be redirected to the login page
  And the session should be terminated

Scenario: Verify logout confirmation message
  When I click on the logout button
  Then a logout confirmation message should be displayed
  And I should be logged out of the system

Scenario: Verify user cannot access application after logout
  Given I have successfully logged out
  When I try to access any protected page directly
  Then I should be redirected to the login page
  And an authentication error should be displayed
