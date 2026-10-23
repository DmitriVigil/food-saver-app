import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity } from 'react-native';

export default function BudgetScreen({ navigation }) {
    const [budget, setBudget] = useState('35.00');
    const [targetMeals, setTargetMeals] = useState('4');

    const goToNextStep = () => {
        // Navigate to Preferences and pass the budget/meals data along
        navigation.navigate('Preferences', {
            budget: parseFloat(budget),
            targetMeals: parseInt(targetMeals)
        });
    };

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Let's plan your week</Text>

            <Text style={styles.label}>Max Grocery Budget ($):</Text>
            <TextInput
                style={styles.input}
                keyboardType="numeric"
                value={budget}
                onChangeText={setBudget}
            />

            <Text style={styles.label}>How many meals do you need?</Text>
            <TextInput
                style={styles.input}
                keyboardType="numeric"
                value={targetMeals}
                onChangeText={setTargetMeals}
            />

            <TouchableOpacity style={styles.button} onPress={goToNextStep}>
                <Text style={styles.buttonText}>Next: Pantry & Allergies ➔</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5', justifyContent: 'center' },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 30, textAlign: 'center' },
    label: { fontSize: 16, marginBottom: 8, fontWeight: '500' },
    input: { borderWidth: 1, borderColor: '#ccc', padding: 15, borderRadius: 8, backgroundColor: '#fff', marginBottom: 20, fontSize: 18 },
    button: { backgroundColor: '#28a745', padding: 18, borderRadius: 8, alignItems: 'center', marginTop: 10 },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});