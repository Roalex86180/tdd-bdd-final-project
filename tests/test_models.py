# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#   P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #   T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=Decimal("12.50"), available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, Decimal("12.50"))
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_find_product_not_found(self):
        """It should not Find a product that does not exist"""
        product = Product.find(0)
        self.assertIsNone(product)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_update_product_no_id(self):
        """It should raise a DataValidationError if update is called with no id"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_list_all_products_empty_database(self):
        """It should return an empty list when the database is empty"""
        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        found = Product.find_by_name(name).all()  # Execute the query
        count = len([product for product in products if product.name == name])
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_nonexistent_name(self):
        """It should return an empty list if no products match the name"""
        found = Product.find_by_name("Nonexistent Product").all() # Execute the query
        self.assertEqual(len(found), 0)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(3)
        for product in products:
            product.create()
        price = products[0].price
        found = Product.find_by_price(price).all() # Execute the query
        count = len([product for product in products if product.price == price])
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_find_by_nonexistent_price(self):
        """It should return an empty list if no products match the price"""
        found = Product.find_by_price(Decimal("999.99")).all() # Execute the query
        self.assertEqual(len(found), 0)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        available_product = ProductFactory(available=True)
        available_product.create()
        unavailable_product = ProductFactory(available=False)
        unavailable_product.create()

        available = Product.find_by_availability(True).all() # Execute the query
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].available, True)

        unavailable = Product.find_by_availability(False).all() # Execute the query
        self.assertEqual(len(unavailable), 1)
        self.assertEqual(unavailable[0].available, False)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(3)
        for product in products:
            product.create()
        category = products[0].category
        found = Product.find_by_category(category).all() # Execute the query
        count = len([product for product in products if product.category == category])
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_products_by_nonexistent_category(self):
        """It should return an empty list if no products match the category"""
        existing_product = ProductFactory(category=Category.CLOTHS)
        existing_product.create()
        found = Product.find_by_category(Category.FOOD).all() # Execute the query
        self.assertEqual(len(found), 0)

