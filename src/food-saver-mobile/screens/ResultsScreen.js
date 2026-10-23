import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, ActivityIndicator, Image, TouchableOpacity } from 'react-native';
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
WebBrowser.maybeCompleteAuthSession();
const API_URL = "http://localhost:8000/api/generate-plan";


export default function ResultsScreen({ route }) {
    // Pull all compiled variables from the previous screens
    const { budget, targetMeals, pantryItems, dislikesAllergies, miscPreferences } = route.params;

    const [loading, setLoading] = useState(true);
    const [mealPlan, setMealPlan] = useState(null);
    const [error, setError] = useState(null);
    const [addingToCart, setAddingToCart] = useState(false);

    // --- NEW: Kroger Auth State & Hooks ---
    const [krogerAuthCode, setKrogerAuthCode] = useState(null);

    const discovery = {
        authorizationEndpoint: 'https://api.kroger.com/v1/connect/oauth2/authorize',
        tokenEndpoint: 'https://api.kroger.com/v1/connect/oauth2/token',
    };

    const [authRequest, authResponse, promptAsync] = AuthSession.useAuthRequest(
        {
            clientId: process.env.EXPO_PUBLIC_KROGER_CLIENT_ID, // Replace with your App's Client ID
            scopes: ['cart.basic:write'],
            redirectUri: AuthSession.makeRedirectUri(),
            responseType: AuthSession.ResponseType.Code,
            usePKCE: false, 
        },
        discovery
    );

    useEffect(() => {
        console.log("AUTH STATUS:", authResponse?.type); // <--- Add this debug line
        if (authResponse?.type === 'success') {
            const { code } = authResponse.params;
            setKrogerAuthCode(code);
            alert("Account linked successfully!");
        }
    }, [authResponse]);
    // ----------------------------------------

    const handleAddToCart = async () => {
        // Prevent adding to cart if not logged in
        if (!krogerAuthCode) {
            alert("Please connect your Kroger account first!");
            return;
        }

        setAddingToCart(true);
        const cartPayload = mealPlan.shopping_list.map(item => ({
            upc: item.upc,
            quantity: 1
        }));

        try {
            const response = await fetch("http://localhost:8000/api/add-to-cart", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // Include auth_code in the payload
                body: JSON.stringify({ items: cartPayload, auth_code: krogerAuthCode })
            });
            const json = await response.json();

            if (json.status === 'success') {
                alert("Success! Ingredients added to your Kroger Cart.");
            } else {
                alert("Failed to add items to cart.");
            }
        } catch (err) {
            console.error(err);
            alert("Network error connecting to the cart API.");
        } finally {
            setAddingToCart(false);
        }
    };

    useEffect(() => {
        const fetchPlan = async () => {
            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        budget: budget,
                        target_meals: targetMeals,
                        pantry_items: pantryItems,
                        dislikes_allergies: dislikesAllergies,
                        misc_preferences: miscPreferences || []
                    })
                });

                const json = await response.json();
                if (json.status === 'success') {
                    setMealPlan(json.data);
                } else {
                    setError("API Error: Could not generate plan.");
                }
            } catch (err) {
                console.error(err);
                setError("Could not connect to the server. Is your Python API running?");
            } finally {
                setLoading(false);
            }
        };

        fetchPlan();
    }, []);

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#28a745" />
                <Text style={styles.loadingText}>Consulting the AI Chef...</Text>
            </View>
        );
    }

    if (error) {
        return (
            <View style={styles.centered}>
                <Text style={styles.errorText}>{error}</Text>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.costText}>
                Estimated Cart Cost: ${mealPlan.actual_calculated_cost.toFixed(2)}
            </Text>

            {mealPlan.recipes.map((recipe, index) => (
                <View key={index} style={styles.card}>
                    <Text style={styles.recipeTitle}>{recipe.name}</Text>
                    <Text style={styles.ingredients}>Ingredients: {recipe.ingredients_used.join(', ')}</Text>
                    <Text style={styles.instructions}>{recipe.instructions}</Text>
                </View>
            ))}

            <Text style={styles.sectionHeader}>Store Shopping List</Text>
            <View style={styles.shoppingListCard}>
                {mealPlan.shopping_list.map((item, index) => (
                    <View key={index} style={styles.shoppingListItem}>
                        {item.image_url ? (
                            <Image
                                source={{ uri: item.image_url }}
                                style={styles.itemImage}
                                resizeMode="contain"
                            />
                        ) : null}
                        <View style={styles.itemTextContainer}>
                            <Text style={styles.itemDescription}>
                                {item.brand !== "Unknown" ? item.brand + " " : ""}{item.description}
                            </Text>
                            <Text style={styles.itemPrice}>${item.price.toFixed(2)}</Text>
                        </View>
                    </View>
                ))}
            </View>

            {/* Checkout Button */}
            {/* Conditional Checkout / Login Buttons */}
            {!krogerAuthCode ? (
                <TouchableOpacity
                    style={[styles.checkoutButton, { backgroundColor: '#e9ecef' }]}
                    disabled={!authRequest}
                    onPress={() => promptAsync()}
                >
                    <Text style={[styles.checkoutButtonText, { color: '#0058a3' }]}>
                        Connect Kroger Account 👤
                    </Text>
                </TouchableOpacity>
            ) : (
                <TouchableOpacity
                    style={styles.checkoutButton}
                    onPress={handleAddToCart}
                    disabled={addingToCart}
                >
                    <Text style={styles.checkoutButtonText}>
                        {addingToCart ? "Adding to Cart..." : "Send to Kroger Cart 🛒"}
                    </Text>
                </TouchableOpacity>
            )}

            <View style={{ height: 40 }} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 15, backgroundColor: '#f5f5f5' },
    centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
    loadingText: { marginTop: 15, fontSize: 18, fontWeight: '500', color: '#555' },
    errorText: { fontSize: 16, color: 'red', textAlign: 'center' },
    costText: { fontSize: 22, fontWeight: 'bold', color: '#28a745', marginBottom: 15, textAlign: 'center', marginTop: 10 },
    card: { backgroundColor: '#fff', padding: 15, borderRadius: 8, marginBottom: 15, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 5, elevation: 3 },
    recipeTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 5 },
    ingredients: { fontStyle: 'italic', color: '#555', marginBottom: 10 },
    instructions: { color: '#333', lineHeight: 20 },
    sectionHeader: { fontSize: 22, fontWeight: 'bold', marginTop: 10, marginBottom: 10, color: '#333' },
    shoppingListCard: { backgroundColor: '#fff', padding: 15, borderRadius: 8, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 5, elevation: 3 },
    shoppingListItem: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#eee' },
    itemDescription: { flex: 1, fontSize: 14, color: '#444', paddingRight: 10 },
    itemPrice: { fontSize: 14, fontWeight: 'bold', color: '#28a745' },
    itemImage: { width: 50, height: 50, marginRight: 12, borderRadius: 6, backgroundColor: '#f0f0f0' },
    itemTextContainer: { flex: 1, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    checkoutButton: { backgroundColor: '#0058a3', padding: 18, borderRadius: 8, alignItems: 'center', marginTop: 20 },
    checkoutButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});