using FactFeelUI;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;

namespace UnitTest.FactFeelView
{
    [TestClass]
    public class FactFeelTests
    {
        [TestMethod]
        public void TestMethod1()
        {
            FactFeelViewModel vm = new FactFeelViewModel();

            Assert.IsNotNull(vm.Config);
        }
    }
}
