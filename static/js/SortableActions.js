const fuentesSeleccionadas = document.getElementById('fuentes-seleccionadas');
const fuentesSugeridas = document.getElementById('fuentes-sugeridas');
$('#guardarSeleccionadas').hide();

Sortable.create(fuentesSeleccionadas, {
	animation: 100, // tiempo de animación al presionar elemento de la lista
	chosenClass: "seleccionado",// clase de cada elemento de la lista
	dragClass: "drag", // clase que se aplica al arrastrar elemento
	delayOnTouchOnly: true, // un retraso en en dispositivos touch
	delay: 200, // tiempo en milisegundos para definir cuando un elemento comienza a arrastrarse
	disabled: false, // lista inhabilitada
	filter: '.locked', // elementos con esta clase no seran arrastrables

	onEnd: (sortable) => {
		// que pasa cuando se termina de arrastrar un elemento a esta lista
		const list  = document.getElementById('fuentes-seleccionadas').children
		if(list.length < maxItems){
			$('#addItems').show();
			$('#guardarSeleccionadas').hide();
		}
	},
	group: {
		name: "lista-personas",
		put: (to) => {
			//la variable maxItems se declara en un bloque script del archivo 'SeleccionFuentes.html'
			return to.el.children.length < maxItems? true: false
		}
	},
	// Element is dropped into the list from another list
	onAdd: function (/**Event*/evt) {
		const list  = document.getElementById('fuentes-seleccionadas').children
		if(list.length < maxItems){
			$('#addItems').show();
			$('#guardarSeleccionadas').hide();
		} else {
			$('#addItems').hide();
			$('#guardarSeleccionadas').show();
		}
		// same properties as onEnd
	},
});

Sortable.create(fuentesSugeridas, {
	animation: 100,
	chosenClass: "seleccionado",
	dragClass: "drag",
	delayOnTouchOnly: true,
	delay: 200,
	disabled: false,
	filter: '.locked',

	group: {
		name: "lista-personas",
		put: (to) => {
			return true
		}
	},
});


$(function() {
	$("#guardarSeleccionadas").button().click(function(e) {
		e.preventDefault();
		//se obtienen los elementos en fuentes sugeridas 
		const list  = document.getElementById('fuentes-seleccionadas').children
		let dataToSave = []
		for( let item of list){
			//hay que filtar las que son sugeridas solamente
			if(item.id == "suggested"){
				dataToSave.push(item.getAttribute('value'))
			}
		}
		
        $.ajax({
			type: "POST",
			url: postUrl,
			dataType: "json",
			headers: headerValues,
			data: {
				'fuentes-preparadas': JSON.stringify(dataToSave)
			},
			success: function() {
			},
			error: function () {
			  },
			complete: function () {
				window.location.href = redirectUrl;

			}
		});
	});
  });