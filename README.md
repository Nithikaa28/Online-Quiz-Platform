# Sarab FoodHub - Online Food Ordering System (Go)

A complete restaurant-style online food ordering web app built with **Go (`net/http`)**, **HTML5**, **CSS3**, and **JavaScript**.

## Tech Stack

- Backend: Go (`net/http` only)
- Template engine: `html/template`
- Frontend: HTML, CSS, JavaScript
- Storage (cart): Browser `localStorage`

## Project Structure

```text
food-ordering-system/
├── main.go
├── go.mod
├── templates/
│   ├── index.html
│   ├── menu.html
│   ├── cart.html
│   ├── checkout.html
│   ├── login.html
│   └── register.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── app.js
    └── images/
```

## Run

```bash
go mod init foodhub
go run main.go
```

Open: `http://localhost:8080`

## Implemented Features

- Sticky navigation bar and responsive layout (desktop/tablet/mobile)
- Hero section with CTA and food search field
- Categories, featured dishes, offers, testimonials, contact, footer
- Menu cards with image/name/description/price/rating
- JavaScript category filtering
- Cart with add/remove/increase/decrease and total amount
- `localStorage` cart persistence
- Checkout form with order summary and success message
- Dark/light theme toggle
- Smooth scrolling and mobile menu toggle
