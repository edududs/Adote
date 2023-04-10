$(document).ready(function() {
    // Máscara de formatação de telefones
    $('input[name="tel"]').mask('(00) 00000-0000');
    // Select estilizado
    $('.select2').select2();
    // API de gráfico de adoções - Dashboard
    fetch("/divulgar/api_adocoes_por_raca/",{
        method: 'GET',
    }).then(function(result){
        return result.json()
    }).then(function(data_adocoes){       
        const data = {
            labels: data_adocoes['labels'],
            datasets: [{
            label: 'Adoções',
            backgroundColor: 'rgb(255, 99, 132)',
            borderColor: 'rgb(255, 99, 132)',
            data: data_adocoes['qtd_adocoes'],
            }]
        };
        const config = {
            type: 'line',
            data: data,
            options: {}
        };
        const myChart = new Chart(
            document.getElementById('myChart'),
            config
        );
    });
    
});
