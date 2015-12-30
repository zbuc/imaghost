package main

import (
	"fmt"
	//"github.com/davecgh/go-spew/spew"
	"html/template"
	"log"
	"net/http"
	"os"
)

type argError struct {
	arg  int
	prob string
}

func (e *argError) Error() string {
	return fmt.Sprintf("%d - %s", e.arg, e.prob)
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	t, _ := template.ParseFiles("templates/index.html")
	p := map[string]interface{}{"Title": "Welcome!"}
	t.Execute(w, p)
}

func main() {
	http.HandleFunc("/", indexHandler)

	log.Println("Running on https://localhost:9666/")

	err := http.ListenAndServeTLS(":9666", "ssl/imag.host.key.crt",
		"ssl/imag.host.key", nil)
	if err != nil {
		// check if it's a os.PathError
		if _, ok := err.(*os.PathError); ok {
			log.Println("Missing cert & key -- try `./make_keys.sh` to" +
				" generate self-signed")
		}

		log.Fatal("ListenAndServeTLS: ", err)
	}
}
