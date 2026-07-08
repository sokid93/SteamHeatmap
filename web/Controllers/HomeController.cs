using Microsoft.AspNetCore.Mvc;
using SteamHeatmap.Web.Domain;

namespace SteamHeatmap.Web.Controllers;

public class HomeController : Controller
{
    private readonly RegionMapViewModelBuilder _viewModelBuilder;

    public HomeController(RegionMapViewModelBuilder viewModelBuilder)
    {
        _viewModelBuilder = viewModelBuilder;
    }

    public async Task<IActionResult> Index()
    {
        var viewModel = await _viewModelBuilder.Build();
        return View(viewModel);
    }
}
