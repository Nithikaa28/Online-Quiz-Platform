package main

import (
	"html/template"
	"log"
	"net/http"
	"path/filepath"
)

// TemplateData stores common data passed to templates.
type TemplateData struct {
	Title string
}

func main() {
	mux := http.NewServeMux()

	// Serve static assets (CSS, JS, images).
	staticHandler := http.FileServer(http.Dir("static"))
	mux.Handle("/static/", http.StripPrefix("/static/", staticHandler))

	mux.HandleFunc("/", renderPage("index.html", "FoodHub | Home"))
	mux.HandleFunc("/menu", renderPage("menu.html", "FoodHub | Menu"))
	mux.HandleFunc("/cart", renderPage("cart.html", "FoodHub | Cart"))
	mux.HandleFunc("/checkout", renderPage("checkout.html", "FoodHub | Checkout"))
	mux.HandleFunc("/login", renderPage("login.html", "FoodHub | Login"))
	mux.HandleFunc("/register", renderPage("register.html", "FoodHub | Register"))

	server := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	log.Println("FoodHub server running at http://localhost:8080")
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server failed: %v", err)
	}
}

// renderPage renders a template file with a strict GET-only handler.
func renderPage(fileName, title string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		if r.URL.Path == "/" || r.URL.Path == "/menu" || r.URL.Path == "/cart" || r.URL.Path == "/checkout" || r.URL.Path == "/login" || r.URL.Path == "/register" {
			renderTemplate(w, fileName, TemplateData{Title: title})
			return
		}

		http.NotFound(w, r)
	}
}

// renderTemplate parses and executes the requested template.
func renderTemplate(w http.ResponseWriter, fileName string, data TemplateData) {
	tmplPath := filepath.Join("templates", fileName)
	tmpl, err := template.ParseFiles(tmplPath)
	if err != nil {
		log.Printf("template parse error (%s): %v", fileName, err)
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	if err := tmpl.Execute(w, data); err != nil {
		log.Printf("template execute error (%s): %v", fileName, err)
		http.Error(w, "internal server error", http.StatusInternalServerError)
	}
}
