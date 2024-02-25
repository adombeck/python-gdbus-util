Feature: D-Bus service
    Test that the D-Bus service works as expected

    Scenario: I can call the D-Bus service and subscribe to signals
        Given The accounts-service is running
        When I subscribe to the UserAdded signal
        And I call the CreateUser method
        Then I should receive the UserAdded signal

    Scenario: I can subscribe to the PropertiesChanged signal
        Given The accounts-service is running
        When I call the CreateUser method
        And I subscribe to the PropertiesChanged signal
        And I call the SetPassword method
        Then I should receive the PropertiesChanged signal

    Scenario: I can handle an error when calling a method
        Given The accounts-service is running
        When I call the CreateUser method
        And I call the SetPassword method with a password that is too short
        Then I should receive an error

    Scenario: I can read properties
        Given The accounts-service is running
        When I call the CreateUser method
        Then I should be able to read the Id property of the user

    Scenario: I can write properties
        Given The accounts-service is running
        When I call the CreateUser method
        And I call the SetPassword method
        Then I should be able to write the Name property of the user
