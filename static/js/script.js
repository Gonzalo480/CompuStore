// Comprobar si estamos en la página de login
const formularioLogin = document.getElementById("formLogin");

if (formularioLogin) {

    formularioLogin.addEventListener("submit", function(event) {

        // Evitar que el formulario recargue la página
        event.preventDefault();

        // Obtener los datos escritos por el usuario
        const usuario = document.getElementById("usuario").value;
        const password = document.getElementById("password").value;

        // Enviar los datos a Flask
        fetch("/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                usuario: usuario,
                password: password
            })

        })

        .then(response => response.json())

        .then(data => {

            if (data.token) {

                // Guardar el token JWT
                localStorage.setItem("token", data.token);

                // Ir directamente al perfil
                window.location.href = "/perfil_pagina";

            } else {

                document.getElementById("mensaje").textContent =
                    data.mensaje;

            }

        })

        .catch(error => {

            console.error("Error:", error);

        });

    });

}


// Acceder a la página de perfil
function accederPerfil() {

    // Obtener el token guardado
    const token = localStorage.getItem("token");

    // Comprobar si existe el token
    if (!token) {

        document.getElementById("perfilMensaje").textContent =
            "No hay una sesión iniciada. Inicia sesión primero.";

        return;
    }

    // Enviar el token a Flask para verificarlo
    fetch("/perfil", {

        method: "GET",

        headers: {
            "Authorization": "Bearer " + token
        }

    })

    .then(response => {

        // Comprobar si Flask rechazó el token
        if (!response.ok) {

            throw new Error("Token inválido");

        }

        return response.json();

    })

    .then(data => {

        // Si el token es válido, abrir el perfil
        window.location.href = "/perfil_pagina";

    })

    .catch(error => {

        console.error("Error:", error);

        document.getElementById("perfilMensaje").textContent =
            "La sesión no es válida. Inicia sesión nuevamente.";

    });

}


// Formulario para agregar productos
const formularioProducto = document.getElementById("formProducto");

if (formularioProducto) {

    formularioProducto.addEventListener("submit", function(event) {

        // Evitar que la página se recargue
        event.preventDefault();

        // Obtener los datos del formulario
        const nombre = document.getElementById("nombre").value;
        const categoria = document.getElementById("categoria").value;
        const precio = document.getElementById("precio").value;
        const stock = document.getElementById("stock").value;

        // Obtener el token guardado
        const token = localStorage.getItem("token");

        // Comprobar si existe el token
        if (!token) {

            document.getElementById("mensajeProducto").textContent =
                "Necesitas iniciar sesión.";

            return;
        }

        // Enviar los datos a Flask
        fetch("/guardar_producto", {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },

            body: JSON.stringify({
                nombre: nombre,
                categoria: categoria,
                precio: precio,
                stock: stock
            })

        })

        .then(response => response.json())

        .then(data => {

            // Mostrar respuesta de Flask
            document.getElementById("mensajeProducto").textContent =
                data.mensaje;

        })

        .catch(error => {

            console.error("Error:", error);

            document.getElementById("mensajeProducto").textContent =
                "Ocurrió un error al guardar el producto.";

        });

    });

}


// Eliminar un producto
function eliminarProducto(id) {

    // Pedir confirmación antes de eliminar
    const confirmar = confirm(
        "¿Estás seguro de que quieres eliminar este producto?"
    );

    // Si el usuario cancela
    if (!confirmar) {

        return;

    }

    // Obtener el token guardado
    const token = localStorage.getItem("token");

    // Comprobar si existe el token
    if (!token) {

        alert("Necesitas iniciar sesión.");

        return;

    }

    // Enviar petición a Flask
    fetch("/eliminar_producto/" + id, {

        method: "DELETE",

        headers: {
            "Authorization": "Bearer " + token
        }

    })

    .then(response => response.json())

    .then(data => {

        // Mostrar el mensaje
        alert(data.mensaje);

        // Actualizar la página
        location.reload();

    })

    .catch(error => {

        console.error("Error:", error);

        alert("Ocurrió un error al eliminar el producto.");

    });

}


// Formulario para editar productos
const formularioEditar = document.getElementById("formEditarProducto");

if (formularioEditar) {

    formularioEditar.addEventListener("submit", function(event) {

        // Evitar que el formulario se recargue
        event.preventDefault();

        // Obtener el ID del producto
        const id = formularioEditar.dataset.id;

        // Obtener los datos modificados
        const nombre = document.getElementById("nombreEditar").value;
        const categoria = document.getElementById("categoriaEditar").value;
        const precio = document.getElementById("precioEditar").value;
        const stock = document.getElementById("stockEditar").value;

        // Obtener el token guardado
        const token = localStorage.getItem("token");

        // Comprobar si existe el token
        if (!token) {

            document.getElementById("mensajeEditar").textContent =
                "Necesitas iniciar sesión.";

            return;
        }

        // Enviar los cambios a Flask
        fetch("/actualizar_producto/" + id, {

            method: "PUT",

            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },

            body: JSON.stringify({
                nombre: nombre,
                categoria: categoria,
                precio: precio,
                stock: stock
            })

        })

        .then(response => response.json())

        .then(data => {

            // Mostrar mensaje
            document.getElementById("mensajeEditar").textContent =
                data.mensaje;

            // Volver a la lista después de actualizar
            setTimeout(function() {

                window.location.href = "/productos_lista";

            }, 1000);

        })

        .catch(error => {

            console.error("Error:", error);

            document.getElementById("mensajeEditar").textContent =
                "Ocurrió un error al actualizar el producto.";

        });

    });

}