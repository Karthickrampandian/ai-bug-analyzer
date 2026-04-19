# Step Definition File for Login Functionality (Kotlin)

kotlin
import io.cucumber.java.en.*

class LoginStepDefinitions {

    // Background Steps
    @Given("I navigate to the login page")
    fun navigateToLoginPage() {
        // Implementation to navigate to login page
    }

    // When Steps
    @When("I enter valid username")
    fun enterValidUsername() {
        // Implementation to enter valid username
    }

    @When("I enter valid password")
    fun enterValidPassword() {
        // Implementation to enter valid password
    }

    @When("I enter invalid username")
    fun enterInvalidUsername() {
        // Implementation to enter invalid username
    }

    @When("I enter invalid password")
    fun enterInvalidPassword() {
        // Implementation to enter invalid password
    }

    @When("I leave username field empty")
    fun leaveUsernameFieldEmpty() {
        // Implementation to leave username field empty
    }

    @When("I leave password field empty")
    fun leavePasswordFieldEmpty() {
        // Implementation to leave password field empty
    }

    @When("I click on login button")
    fun clickLoginButton() {
        // Implementation to click login button
    }

    // Then Steps
    @Then("I should be logged in successfully")
    fun verifySuccessfulLogin() {
        // Implementation to verify successful login
    }

    @Then("I should be redirected to the home page")
    fun verifyRedirectionToHomePage() {
        // Implementation to verify redirection to home page
    }

    @Then("I should see an error message")
    fun verifyErrorMessage() {
        // Implementation to verify error message is displayed
    }

    @Then("I should see a validation error")
    fun verifySingleValidationError() {
        // Implementation to verify single validation error
    }

    @Then("I should see validation errors")
    fun verifyMultipleValidationErrors() {
        // Implementation to verify multiple validation errors
    }

    @Then("I should remain on the login page")
    fun verifyRemainsOnLoginPage() {
        // Implementation to verify user remains on login page
    }
}


## Summary of Step Definitions Created:

### Background (1 step)
- Navigate to login page

### When Clauses (7 steps)
- Enter valid username
- Enter valid password
- Enter invalid username
- Enter invalid password
- Leave username field empty
- Leave password field empty
- Click on login button

### Then Clauses (6 steps)
- Logged in successfully
- Redirected to home page
- See an error message
- See a validation error
- See validation errors (plural)
- Remain on login page

**Total: 14 unique step definitions** (duplicates removed as per requirements)