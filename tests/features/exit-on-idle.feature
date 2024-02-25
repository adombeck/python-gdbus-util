Feature: exit-on-idle service
    Test that the exit-on-idle service behaves as expected

    Scenario: The service exits after the idle timeout
        Given sleeper-service is running with a 1 second idle timeout
        Then sleeper-service should be running
        When I wait for 2.0 seconds
        Then sleeper-service should not be running

    Scenario: Calling the service resets the idle timeout
        Given sleeper-service is running with a 2 second idle timeout
        When I wait for 1.5 seconds
        And I call a method of the sleeper-service
        And I wait for another 1.5 seconds
        Then sleeper-service should be running
        When I wait for another 1.0 seconds
        Then sleeper-service should not be running

    Scenario: Calling a sub-object of the service also resets the idle timeout
        Given sleeper-service is running with a 2 second idle timeout
        When I wait for 1.5 seconds
        And I call a method of a sub-object of the sleeper-service
        And I wait for another 1.5 seconds
        Then sleeper-service should be running
        When I wait for another 1.0 seconds
        Then sleeper-service should not be running

    Scenario: The service does not exit if it is not idle
        Given sleeper-service is running with a 1 second idle timeout
        When I let the sleeper-service sleep for 2 seconds
        Then sleeper-service should be running
        When I wait for 2.0 seconds
        Then sleeper-service should not be running

    Scenario: The service also does not exit if a sub-object is not idle
        Given sleeper-service is running with a 1 second idle timeout
        When I let a sub-object of the sleeper-service sleep for 2 seconds
        Then sleeper-service should be running
        When I wait for 2.0 seconds
        Then sleeper-service should not be running
