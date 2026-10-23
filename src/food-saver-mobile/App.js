import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Import our future screens
import BudgetScreen from './screens/BudgetScreen';
import PreferencesScreen from './screens/PreferencesScreen';
import ResultsScreen from './screens/ResultsScreen';

const Stack = createNativeStackNavigator();

export default function App() {
    return (
        <NavigationContainer>
            <Stack.Navigator initialRouteName="Budget">
                <Stack.Screen
                    name="Budget"
                    component={BudgetScreen}
                    options={{ title: 'Step 1: Weekly Budget' }}
                />
                <Stack.Screen
                    name="Preferences"
                    component={PreferencesScreen}
                    options={{ title: 'Step 2: Pantry & Diet' }}
                />
                <Stack.Screen
                    name="Results"
                    component={ResultsScreen}
                    options={{ title: 'Your Meal Plan' }}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
}