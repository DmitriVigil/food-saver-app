import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from 'react-native';

// Pre-defined options (Emojis act as placeholders for future stock photos)
// Pre-defined options (Emojis act as placeholders for future stock photos)
const PANTRY_OPTIONS = [
    { id: 'rice', label: 'Rice', icon: '🍚' },
    { id: 'pasta', label: 'Pasta', icon: '🍝' },
    { id: 'eggs', label: 'Eggs', icon: '🥚' },
    { id: 'milk', label: 'Milk', icon: '🥛' },
    { id: 'garlic', label: 'Garlic', icon: '🧄' },
    { id: 'butter', label: 'Butter', icon: '🧈' },
    { id: 'cheese', label: 'Cheese', icon: '🧀' },
    { id: 'chicken_breast', label: 'Chicken Breast', icon: '🍗' },
    { id: 'ground_beef', label: 'Ground Beef', icon: '🥩' },
    { id: 'beans', label: 'Beans', icon: '🫘' },
    { id: 'tomatoes', label: 'Tomatoes', icon: '🍅' },
    { id: 'spinach', label: 'Spinach', icon: '🥬' },
    { id: 'onions', label: 'Onions', icon: '🧅' },
    { id: 'potatoes', label: 'Potatoes', icon: '🥔' },
    { id: 'olive_oil', label: 'Olive Oil', icon: '🫒' },
    { id: 'salt', label: 'Salt', icon: '🧂' }
];

const DISLIKE_OPTIONS = [
    // Common strong flavors & aversions
    { id: 'mushrooms', label: 'Mushrooms', icon: '🍄' },
    { id: 'olives', label: 'Olives', icon: '🫒' },
    { id: 'cilantro', label: 'Cilantro', icon: '🌿' },
    { id: 'spicy', label: 'Spicy Food', icon: '🌶️' },
    { id: 'seafood', label: 'Fish/Seafood', icon: '🐟' },
    { id: 'pork', label: 'Pork', icon: '🥓' },
    { id: 'bell_peppers', label: 'Bell Peppers', icon: '🫑' },
    { id: 'eggplant', label: 'Eggplant', icon: '🍆' },
    { id: 'mayo', label: 'Mayonnaise', icon: '🥚' }, // Covering the mayo example

    // Database-specific ingredients that are commonly disliked
    { id: 'onions', label: 'Onions', icon: '🧅' },
    { id: 'garlic', label: 'Garlic', icon: '🧄' },
    { id: 'tomatoes', label: 'Tomatoes', icon: '🍅' },
    { id: 'beans', label: 'Beans', icon: '🫘' },
    { id: 'spinach', label: 'Spinach', icon: '🥬' }
];

const DIET_ALLERGY_OPTIONS = [
    { id: 'high_protein', label: 'High Protein', icon: '🥩' },
    { id: 'healthy', label: 'Low Calorie', icon: '🥗' },
    { id: 'vegetarian', label: 'Vegetarian', icon: '🥦' },
    { id: 'vegan', label: 'Vegan', icon: '🌱' },
    { id: 'keto', label: 'Keto', icon: '🥑' },
    { id: 'gluten_free', label: 'Gluten-Free', icon: '🚫🌾' },
    { id: 'dairy_free', label: 'Dairy-Free', icon: '🚫🥛' },
    { id: 'peanut_allergy', label: 'No Peanuts', icon: '🚫🥜' },
    { id: 'tree_nut_allergy', label: 'No Tree Nuts', icon: '🚫🌰' },
    { id: 'soy_allergy', label: 'No Soy', icon: '🚫🫘' },
    { id: 'shellfish_allergy', label: 'No Shellfish', icon: '🚫🦐' }
];

const MISC_OPTIONS = [
    { id: 'college', label: 'College Student (No Oven)', icon: '🎓' },
    { id: 'quick', label: 'Quick Meal (< 15 mins)', icon: '⏱️' },
    { id: 'microwave', label: 'Microwave Only', icon: '♨️' },
    { id: 'meal_prep', label: 'Good for Leftovers', icon: '🥡' }
];
export default function PreferencesScreen({ route, navigation }) {
    const { budget, targetMeals } = route.params;

    // States to hold the selected buttons
    const [pantry, setPantry] = useState([]);
    const [dislikes, setDislikes] = useState([]);
    const [diets, setDiets] = useState([]);
    const [misc, setMisc] = useState([]);

    // Generic toggle function for the chips
    const toggleSelection = (itemLabel, currentList, setList) => {
        if (currentList.includes(itemLabel)) {
            setList(currentList.filter(i => i !== itemLabel));
        } else {
            setList([...currentList, itemLabel]);
        }
    };

    // Reusable component to render the grids of buttons
    const renderButtons = (options, currentList, setList) => (
        <View style={styles.buttonRow}>
            {options.map((item) => {
                const isSelected = currentList.includes(item.label);
                return (
                    <TouchableOpacity
                        key={item.id}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => toggleSelection(item.label, currentList, setList)}
                    >
                        {/* Future stock photos will replace this Text element */}
                        <Text style={styles.chipIcon}>{item.icon}</Text>
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                            {item.label}
                        </Text>
                    </TouchableOpacity>
                );
            })}
        </View>
    );

    const generatePlan = () => {
        // Pass everything to ResultsScreen
        navigation.navigate('Results', {
            budget,
            targetMeals,
            pantryItems: pantry,
            dislikesAllergies: [...diets,...dislikes], // Grouped diets/allergies together for now
            miscPreferences: misc
        });
    };

    return (
        <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
            <Text style={styles.header}>Customize Your Plan</Text>

            <Text style={styles.label}>What do you already have?</Text>
            {renderButtons(PANTRY_OPTIONS, pantry, setPantry)}

            <Text style={styles.label}>Things you dislike:</Text>
            {renderButtons(DISLIKE_OPTIONS, dislikes, setDislikes)}

            <Text style={styles.label}>Diets & Allergies:</Text>
            {renderButtons(DIET_ALLERGY_OPTIONS, diets, setDiets)}

            <Text style={styles.label}>Cooking Style & Equipment:</Text>
            {renderButtons(MISC_OPTIONS, misc, setMisc)}

            <TouchableOpacity style={styles.button} onPress={generatePlan}>
                <Text style={styles.buttonText}>Generate Meal Plan ➔</Text>
            </TouchableOpacity>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5' },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    label: { fontSize: 18, marginTop: 15, marginBottom: 10, fontWeight: 'bold', color: '#333' },
    buttonRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 15 },

    // Chip Styling
    chip: {
        flexDirection: 'row',
        backgroundColor: '#fff',
        paddingVertical: 12,
        paddingHorizontal: 16,
        borderRadius: 25,
        margin: 6,
        borderWidth: 1,
        borderColor: '#ddd',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 3,
        elevation: 2
    },
    chipSelected: { backgroundColor: '#28a745', borderColor: '#28a745' },
    chipIcon: { fontSize: 20, marginRight: 8 },
    chipText: { fontSize: 15, color: '#444', fontWeight: '600' },
    chipTextSelected: { color: '#fff' },

    button: { backgroundColor: '#28a745', padding: 18, borderRadius: 8, alignItems: 'center', marginTop: 30 },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});